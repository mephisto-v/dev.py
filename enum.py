#!/usr/bin/env python3
import sys
from scapy.all import *
from collections import defaultdict
from termcolor import colored

def parse_encryption(pkt, bssid, enc_dict):
    # WPA/WPA2/WPA3 detection via RSN and WPA information elements
    if pkt.haslayer(Dot11Elt):
        elt = pkt.getlayer(Dot11Elt)
        while isinstance(elt, Dot11Elt):
            if elt.ID == 48:  # RSN (Robust Security Network) = WPA2 or WPA3
                # Parse cipher suite and AKM suite
                data = elt.info
                version = int.from_bytes(data[0:2], 'little')
                # Count AKM suite list
                akm_count = int.from_bytes(data[10:12], 'little') if len(data) > 11 else 0
                # AKM suite types (WPA2, WPA3, etc.)
                akm = []
                for i in range(akm_count):
                    base = 12 + i*4
                    if len(data) >= base+4:
                        suite = data[base:base+4]
                        if suite == b'\x00\x0f\xac\x08':  # 802.1X SAE (WPA3)
                            akm.append("WPA3")
                        elif suite == b'\x00\x0f\xac\x02':  # PSK
                            akm.append("WPA2")
                        elif suite == b'\x00\x0f\xac\x06':  # 802.1X FT-PSK (WPA2)
                            akm.append("WPA2")
                        elif suite == b'\x00\x0f\xac\x01':  # 802.1X (WPA2)
                            akm.append("WPA2")
                        elif suite == b'\x00\x0f\xac\x03':
                            akm.append("WPA2")
                        elif suite == b'\x00\x0f\xac\x12':  # OWE (Enhanced Open)
                            akm.append("OPN")
                        else:
                            akm.append("WPA2")
                if not akm:
                    enc_dict[bssid].add("WPA2")
                else:
                    for e in akm:
                        enc_dict[bssid].add(e)
            elif elt.ID == 221 and elt.info.startswith(b'\x00\x50\xf2\x01'):  # WPA (old)
                enc_dict[bssid].add("WPA")
            elif elt.ID == 221 and elt.info.startswith(b'\x50\x6f\x9a\x1a'):  # OWE
                enc_dict[bssid].add("OPN")
            elt = elt.payload.getlayer(Dot11Elt)
    # WEP detection
    if pkt.haslayer(Dot11Beacon) or pkt.haslayer(Dot11ProbeResp):
        cap = pkt.sprintf("{Dot11Beacon:%Dot11Beacon.cap%}"
                          "{Dot11ProbeResp:%Dot11ProbeResp.cap%}")
        if "privacy" in cap.lower():
            # If no WPA/WPA2/WPA3 detected, it's WEP
            if not enc_dict[bssid]:
                enc_dict[bssid].add("WEP")
        else:
            if not enc_dict[bssid]:
                enc_dict[bssid].add("OPN")

def parse_info(bssid, handshakes, wep_ivs):
    info = ""
    if wep_ivs.get(bssid, 0) > 5000:
        info = colored("WEP Handshake", "yellow")
    elif handshakes.get(bssid) == "WPA":
        info = colored("WPA Handshake", "cyan")
    elif handshakes.get(bssid) == "WPA-PMKID":
        info = colored("WPA PMKID", "magenta")
    return info

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <capture>")
        sys.exit(1)
    capture = sys.argv[1]
    networks = {}
    essids = {}
    enc_dict = defaultdict(set)
    wep_ivs = defaultdict(int)
    handshakes = {}
    seen_pmkid = set()

    # Read packets and parse
    packets = rdpcap(capture)
    for pkt in packets:
        if pkt.haslayer(Dot11Beacon) or pkt.haslayer(Dot11ProbeResp):
            bssid = pkt[Dot11].addr2
            networks[bssid] = pkt
            # Get the ESSID
            essid = pkt[Dot11Elt].info.decode('utf-8', errors='replace') if pkt[Dot11Elt].ID == 0 else "<hidden>"
            essids[bssid] = essid.strip()
            parse_encryption(pkt, bssid, enc_dict)
        # WEP IVs detection (Data frames with WEP bit set)
        if pkt.haslayer(Dot11):
            bssid = pkt[Dot11].addr2
            if pkt.haslayer(Dot11WEP):
                wep_ivs[bssid] += 1
        # WPA/WPA2 handshake detection (EAPOL)
        if pkt.haslayer(EAPOL):
            bssid = pkt[Dot11].addr2
            handshakes[bssid] = "WPA"
        # WPA3/PMKID detection
        if pkt.haslayer(Dot11Elt) and pkt.type == 0 and pkt.subtype == 8:  # Beacon
            elt = pkt.getlayer(Dot11Elt)
            while isinstance(elt, Dot11Elt):
                if elt.ID == 221 and elt.info.startswith(b'\x50\x6f\x9a\x1a'):
                    bssid = pkt[Dot11].addr2
                    handshakes[bssid] = "WPA-PMKID"
                    seen_pmkid.add(bssid)
                elt = elt.payload.getlayer(Dot11Elt)

    # Format the results
    print(colored("SELECT A TARGET:", "green", attrs=["bold"]))
    header = f"{'#':<3} {'BSSID':<17} {'ESSID':<25} {'Encryption':<18} {'INFO'}"
    print(colored(header, "white", attrs=["bold", "underline"]))
    output = []
    for i, (bssid, pkt) in enumerate(networks.items(), 1):
        essid = essids.get(bssid, "<hidden>")
        enc_types = sorted(enc_dict[bssid], key=lambda x: ("OPN", "WEP", "WPA", "WPA2", "WPA3", "WPA2/WPA3", "WPA/WPA2").index(x) if x in ("OPN", "WEP", "WPA", "WPA2", "WPA3", "WPA2/WPA3", "WPA/WPA2") else 100)
        # Compose Encryption field
        enc = "Unknown"
        if enc_types:
            if set(enc_types) == {"WPA2", "WPA3"}:
                enc = "WPA2/WPA3"
            elif set(enc_types) == {"WPA", "WPA2"}:
                enc = "WPA/WPA2"
            else:
                enc = "/".join(enc_types)
        info = parse_info(bssid, handshakes, wep_ivs)
        # Colorize encryption
        enc_color = {
            "OPN": "green",
            "WEP": "yellow",
            "WPA": "cyan",
            "WPA2": "blue",
            "WPA3": "magenta",
            "WPA2/WPA3": "magenta",
            "WPA/WPA2": "blue",
            "Unknown": "red"
        }.get(enc, "white")
        print(f"{str(i):<3} {bssid:<17} {essid:<25} {colored(enc, enc_color, attrs=['bold']):<18} {info}")

    print()
    sel = input(colored(f"Select network [1-{len(networks)}]: ", "cyan", attrs=["bold"]))
    try:
        sel = int(sel)
        if sel < 1 or sel > len(networks):
            raise ValueError
    except Exception:
        print(colored("Invalid selection!", "red"))
        sys.exit(1)
    bssid = list(networks.keys())[sel - 1]
    print(colored(f"Selected BSSID: {bssid}, ESSID: {essids.get(bssid, '<hidden>')}", "green"))

if __name__ == "__main__":
    main()
