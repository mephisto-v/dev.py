#!/usr/bin/env python3
import sys
import argparse
from scapy.all import *
from scapy.layers.dot11 import Dot11, Dot11Elt, RadioTap
from collections import defaultdict, Counter
from termcolor import colored

# --- Wireless Encryption Identifiers ---
WPA_SUITES = {
    1: "WEP40",
    2: "TKIP",
    4: "CCMP",
    5: "WEP104",
    6: "BIP",
    8: "GCMP",
    9: "GCMP-256",
    10: "CCMP-256"
}
AKM_SUITES = {
    1: "WPA-PSK",
    2: "WPA-802.1X",
    3: "FT-PSK",
    4: "FT-802.1X",
    5: "WPA-PSK-SHA256",
    6: "WPA-802.1X-SHA256",
    7: "TDLS",
    8: "SAE", # WPA3
    9: "FT-SAE",
    11: "WPA3-802.1X",
    12: "WPA3-FT-802.1X",
    13: "WPA3-PMK",
    14: "WPA3-FT-PMK",
    16: "OWE",
    18: "DPP",
}

def parse_args():
    parser = argparse.ArgumentParser(description="Parse BSSID/ESSID/encryption from capture file")
    parser.add_argument("capture", help="Path to .cap/.pcap/.pcapng file")
    return parser.parse_args()

def get_essid(pkt):
    if not pkt.haslayer(Dot11Elt):
        return ""
    elt = pkt[Dot11Elt]
    while isinstance(elt, Dot11Elt):
        if elt.ID == 0:
            try:
                return elt.info.decode(errors='ignore')
            except:
                return ""
        elt = elt.payload
    return ""

def parse_rsn_info(rsn_bytes):
    """Parse RSN Information Element for WPA2/WPA3"""
    enc = set()
    akms = set()
    mgmt = set()
    try:
        version = int.from_bytes(rsn_bytes[0:2], "little")
        # Group Cipher Suite
        group_cipher = rsn_bytes[2:6]
        group_oui = group_cipher[:3]
        group_suite = group_cipher[3]
        enc.add(WPA_SUITES.get(group_suite, "Unknown"))

        # Pairwise Cipher Suite Count
        pcs_count = int.from_bytes(rsn_bytes[6:8], "little")
        offset = 8
        for _ in range(pcs_count):
            pcs = rsn_bytes[offset:offset+4]
            suite = pcs[3]
            enc.add(WPA_SUITES.get(suite, "Unknown"))
            offset += 4

        # AKM Suite Count
        akm_count = int.from_bytes(rsn_bytes[offset:offset+2], "little")
        offset += 2
        for _ in range(akm_count):
            akm = rsn_bytes[offset:offset+4]
            suite = akm[3]
            akms.add(AKM_SUITES.get(suite, f"Unknown({suite})"))
            offset += 4

        # RSN Capabilities
        offset += 2
        # PMKID count
        if len(rsn_bytes) > offset:
            pmkid_count = int.from_bytes(rsn_bytes[offset:offset+2], "little")
            offset += 2 + pmkid_count*16
        # Group Management Cipher Suite (WPA3)
        if len(rsn_bytes) >= offset+4:
            mgmt_cipher = rsn_bytes[offset:offset+4]
            mgmt_suite = mgmt_cipher[3]
            mgmt.add(WPA_SUITES.get(mgmt_suite, "Unknown"))
    except Exception:
        pass
    return enc, akms, mgmt

def parse_wpa_info(wpa_bytes):
    """Parse WPA (vendor specific) Information Element for WPA/WPA2"""
    # WPA IE is similar to RSN but inside vendor specific element
    return parse_rsn_info(wpa_bytes)

def get_encryption(pkt):
    """Determine encryption methods, suites, and AKM"""
    enc = set()
    akms = set()
    mgmt = set()
    is_wep = False
    is_wpa = False
    is_wpa2 = False
    is_wpa3 = False
    is_owe = False
    is_opn = False
    info = []
    if not pkt.haslayer(Dot11Elt):
        return ("Unknown", "(Unknown)", "-")
    capability = pkt.sprintf("{Dot11Beacon:%Dot11Beacon.cap%}").split('+')
    if 'privacy' in capability:
        is_wep = True
    elt = pkt[Dot11Elt]
    while isinstance(elt, Dot11Elt):
        if elt.ID == 48:  # RSN
            is_wpa2 = True
            suites, akm, mgmt_cipher = parse_rsn_info(elt.info)
            enc |= suites
            akms |= akm
            mgmt |= mgmt_cipher
            if any("SAE" in a or "WPA3" in a for a in akm):
                is_wpa3 = True
            if "OWE" in akm:
                is_owe = True
        elif elt.ID == 221 and elt.info.startswith(b'\x00\x50\xf2\x01'):
            # WPA1 Vendor Specific
            is_wpa = True
            suites, akm, mgmt_cipher = parse_wpa_info(elt.info[4:])
            enc |= suites
            akms |= akm
        elt = elt.payload

    if is_wpa3 or (akms and any("SAE" in a or "WPA3" in a for a in akms)):
        encryption = "WPA3"
    elif is_wpa2 and is_wpa:
        encryption = "WPA/WPA2"
    elif is_wpa2:
        encryption = "WPA2"
    elif is_wpa:
        encryption = "WPA"
    elif is_owe:
        encryption = "OPN"
    elif is_wep:
        encryption = "WEP"
    else:
        encryption = "OPN"
        is_opn = True

    # Compose details
    suite_str = ""
    if enc or akms or mgmt:
        suite_parts = []
        if enc: suite_parts.append("/".join(sorted(enc)))
        if akms: suite_parts.append("/".join(sorted(akms)))
        if mgmt: suite_parts.append("MGT:" + "/".join(sorted(mgmt)))
        suite_str = "(" + ", ".join(suite_parts) + ")"
    else:
        suite_str = "(None)"

    return (encryption, suite_str, "-")

def get_bssid(pkt):
    return pkt[Dot11].addr3 if pkt.haslayer(Dot11) else ""

def get_handshake_info(bssid, packets, iv_counter, handshakes, pmkids):
    info = ""
    if iv_counter.get(bssid, 0) > 5000:
        info = "WEP Handshake"
    elif bssid in handshakes:
        info = "WPA Handshake"
    elif bssid in pmkids:
        info = "PMKID"
    else:
        info = "-"
    return info

def detect_handshakes(packets):
    handshakes = set()
    pmkids = set()
    iv_counter = Counter()
    for pkt in packets:
        if pkt.haslayer(Dot11):
            if pkt.type == 2 and pkt.haslayer(Dot11WEP):
                # Data encrypted with WEP
                bssid = pkt[Dot11].addr3
                iv = pkt.iv
                iv_counter[bssid] += 1
            elif pkt.haslayer(EAPOL):
                # WPA handshake
                bssid = pkt[Dot11].addr3
                handshakes.add(bssid)
            elif pkt.haslayer(Dot11Elt):
                elt = pkt[Dot11Elt]
                while isinstance(elt, Dot11Elt):
                    if elt.ID == 221 and elt.info.startswith(b'\x50\x6f\x9a\x0e'):
                        # PMKID
                        bssid = pkt[Dot11].addr3
                        pmkids.add(bssid)
                    elt = elt.payload
    return iv_counter, handshakes, pmkids

def colorize(text, enc_type):
    color_map = {
        "WEP": "red",
        "WPA": "yellow",
        "WPA2": "yellow",
        "WPA3": "green",
        "OPN": "cyan"
    }
    color = color_map.get(enc_type.split("/")[0], "white")
    return colored(text, color, attrs=["bold"])

def main():
    args = parse_args()
    capfile = args.capture

    # Parse packets
    try:
        packets = rdpcap(capfile)
    except Exception as e:
        print(f"Error loading capture file: {e}")
        sys.exit(1)

    networks = {}
    # Pre-detect handshakes and iv counters
    iv_counter, handshakes, pmkids = detect_handshakes(packets)

    for pkt in packets:
        if pkt.haslayer(Dot11Beacon) or pkt.haslayer(Dot11ProbeResp):
            bssid = get_bssid(pkt)
            essid = get_essid(pkt)
            enc_type, enc_detail, _ = get_encryption(pkt)
            info = get_handshake_info(bssid, packets, iv_counter, handshakes, pmkids)
            if bssid not in networks:
                networks[bssid] = {
                    "essid": essid,
                    "encryption": enc_type,
                    "encryption_detail": enc_detail,
                    "info": info
                }

    # Print Table
    print(colored("SELECT A TARGET:", attrs=["bold"]))
    print(colored("#   BSSID              ESSID                     Encryption         INFO", "white", attrs=["bold"]))
    for idx, (bssid, data) in enumerate(networks.items(), 1):
        essid = data["essid"] if data["essid"] else "<HIDDEN>"
        enc = colorize(f"{data['encryption']:<7}", data['encryption'])
        enc_detail = colorize(f"{data['encryption_detail']:<20}", data['encryption'])
        info = colorize(f"{data['info']:<15}", data['encryption'])
        print(f"{idx:<3} {bssid:<18} {essid:<25} {enc} {enc_detail} {info}")

    # Prompt user selection
    if networks:
        min_idx, max_idx = 1, len(networks)
        sel = ""
        while not (str(sel).isdigit() and min_idx <= int(sel) <= max_idx):
            sel = input(f"Select network [{min_idx}-{max_idx}]: ").strip()
        sel = int(sel)
        bssid = list(networks.keys())[sel-1]
        print(colored(f"Selected BSSID: {bssid} (ESSID: {networks[bssid]['essid']})", "green", attrs=["bold"]))
    else:
        print("No networks found.")

if __name__ == "__main__":
    main()
