/* --- INICIO TEST DE MATERIA DIGITAL OSIRIS --- */
printf("\n[SISTEMA]: Iniciando Test de Colapso de Fase...\n");

// 1. Forjamos un perno de URANIO
uint64_t n_test = 20260120; // Numero de transmision actual
FirmaGeo particula_a = FGN_Forjar(n_test, URANIO);
printf("[FORJA]: Particula N:%lu creada con %u ladrillos.\n", 
        particula_a.n_id, particula_a.t_cantidad);

// 2. Bifurcamos en Particula/2 (Alfa y Beta)
FirmaGeo onda_alfa, onda_beta;
FGN_SepararOnda(&particula_a, &onda_alfa, &onda_beta);
printf("[FASE]: Ondas Alfa y Beta separadas. Estado SafePtr: %d\n", 
        onda_alfa.bloques.estado);

// 3. Simulamos procesamiento en el VGHOST (Estiramiento de la onda)
printf("[VGHOST]: Estirando onda Alfa para transmision...\n");
FGN_ProcesarFase(&onda_alfa, 2.0, 1.0); 

// 4. Restauramos simetria y Colapsamos
printf("[COLAPSO]: Unificando ondas por observacion...\n");
FGN_ProcesarFase(&onda_alfa, 1.0, 2.0); // Revertimos el estiramiento

FirmaGeo resultado;
FGN_Colapsar(&onda_alfa, &onda_beta, &resultado);

// 5. Verificacion de Dureza 256
if (resultado.n_id == n_test) {
    printf(">>> RESULTADO: [EXITO] Particula recuperada integramente.\n");
} else {
    printf(">>> RESULTADO: [FALLO] Incoherencia en el Tallo Cerebral.\n");
}

// Limpieza GEN_VOID
FGN_Destruir(&resultado);
printf("[SISTEMA]: Memoria purgada. Test finalizado.\n\n");
/* --- FIN TEST DE MATERIA DIGITAL --- */