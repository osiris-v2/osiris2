#ifndef ODS_PROTOCOLO_H
#define ODS_PROTOCOLO_H

#define PUERTO_OSIRIS 8080
#define CABECERA_MAGICA 0x256F 

typedef struct {
    unsigned short magic;
    unsigned int hash_verif;
    unsigned long longitud;
    char data[4096];
} __attribute__((packed)) PaqueteSoberano; 
// Usamos packed para que GCC no añada padding y Rust lo lea igual

#endif