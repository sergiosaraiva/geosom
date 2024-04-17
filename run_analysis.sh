#!/bin/bash
python main.py "data/BGRI21_170.gpkg" "data/output" --attributes N_ALOJAMENTOS_TOTAL,N_ALOJAMENTOS_FAMILIARES,N_NUCLEOS_FAMILIARES,N_NUCLEOS_FAMILIARES_COM_FILHOS_TENDO_O_MAIS_NOVO_MENOS_DE_25,N_INDIVIDUOS,N_INDIVIDUOS_H,N_INDIVIDUOS_M,N_INDIVIDUOS_0_14,N_INDIVIDUOS_15_24,N_INDIVIDUOS_25_64,N_INDIVIDUOS_65_OU_MAIS --sigma 1 --cell_size 0.5 --som_x 10 --som_y 10 --num_iterations 500