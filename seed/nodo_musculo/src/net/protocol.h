#ifndef PROTOCOL_H
#define PROTOCOL_H
#include <stdint.h>

#pragma pack(push, 1)
typedef struct {
    uint8_t  version;      // 1 byte
    uint8_t  seed_id;      // 1 byte
    uint16_t opcode;       // 2 bytes
    uint32_t payload_size; // 4 bytes
    uint32_t signature;    // 4 bytes
} OsirisPacket;            // Total: 12 bytes
#pragma pack(pop)
#endif