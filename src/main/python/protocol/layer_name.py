# SPDX-License-Identifier: GPL-2.0-or-later
import struct

from protocol.base_protocol import BaseProtocol
from protocol.constants import CMD_VIA_VIAL_PREFIX, CMD_VIAL_DYNAMIC_ENTRY_OP, DYNAMIC_VIAL_LAYER_NAME_GET, \
    DYNAMIC_VIAL_LAYER_NAME_SET
from unlocker import Unlocker


LAYER_NAME_LEN = 16

class ProtocolLayerName(BaseProtocol):
    def reload_layer_names(self):
        # Cache names for all layers
        self.layer_names = []
        for (raw,) in self._retrieve_dynamic_entries(DYNAMIC_VIAL_LAYER_NAME_GET, self.layers, f"{LAYER_NAME_LEN}s"):
            self.layer_names.append(raw.split(b'\x00', 1)[0].decode('utf-8', errors='ignore'))
    
    def layer_name_get(self, layer):
        msg = struct.pack("BBBB", CMD_VIA_VIAL_PREFIX, CMD_VIAL_DYNAMIC_ENTRY_OP, DYNAMIC_VIAL_LAYER_NAME_GET, layer)

        resp = self.usb_send(self.dev, msg, retries=20)

        if resp[0] != 0:
            raise RuntimeError(f"Failed getting layer name for layer {layer}, status code: {resp[0]}")
        
        raw = resp[1:1 + LAYER_NAME_LEN].split(b'\x00', 1)[0]
        return raw.decode('utf-8', errors='ignore')
    
    def layer_name_set(self, layer, name):
        raw = name.encode('utf-8', errors='ignore')[:LAYER_NAME_LEN]  # Truncate to max length
        raw = raw + b'\x00' * (LAYER_NAME_LEN - len(raw))  # Pad with null bytes

        Unlocker.unlock(self)

        msg = struct.pack("BBBB", CMD_VIA_VIAL_PREFIX, CMD_VIAL_DYNAMIC_ENTRY_OP, DYNAMIC_VIAL_LAYER_NAME_SET, layer) + raw

        resp = self.usb_send(self.dev, msg, retries=20)

        if resp[0] != 0:
            raise RuntimeError(f"Failed setting layer name for layer {layer}, status code: {resp[0]}")
        
        got = self.layer_name_get(layer)

        sent = raw.split(b'\x00', 1)[0].decode('utf-8', errors='ignore')
        if got != sent:
            raise RuntimeError(f"Verification failed for layer name set. Sent: '{sent}', Got: '{got}'")

        if hasattr(self, 'layer_names') and layer < len(self.layer_names):
            sent = raw.split(b'\x00', 1)[0].decode('utf-8', errors='ignore')
            self.layer_names[layer] = sent
        