'''
Este programa permite obtener el formato 1 de RRHH del SIGCOM. Unidad de Finanzas.
Javier Rojas Benítez.'''

import pandas as pd
import json
import os


class ModuloRecursosHumanosSIGCOM:
    def __init__(self):
        pass

    def correr_programa(self):
        df_leyes_juntas, honorarios = self.cargar_archivos_y_formatearlos()
        suma_por_funcionario = self.agrupar_dfs(df_leyes_juntas, honorarios, 'funcionario')
        suma_por_unidad = self.agrupar_dfs(df_leyes_juntas, honorarios, 'unidad')

        guardar_archivos(suma_por_funcionario, suma_por_unidad)

    def cargar_archivos_y_formatearlos(self):
        '''
        Este función permite obtener los archivos de RRHH, tanto para los funcionarios contratados
        por Leyes, como los funcionarios que prestan servicios por Honorarios.

        En este caso, las 3 leyes del Hospital son juntadas en una única tabla.

        Las Columnas que se dejan tanto en Leyes, como Honorario, son:
         - ['RUT-DV', 'NOMBRE', 'UNIDAD', 'CARGO', 'TOTAL HABER']'''

        print(f'{"SE ESTÁN CARGANDO LOS ARCHIVOS":-^40}')
        leyes = self.cargar_leyes()
        honorarios = self.cargar_honorarios()
        leyes_procesada, honorarios_procesada = self.unificar_formatos(leyes, honorarios)

        return leyes_procesada, honorarios_procesada

    def cargar_leyes(self):
        '''
        Esta función permite cargar los archivos de funcionarios contratados por Leyes.
        - Los archivos considerados como leyes, son todos los que tengan el string "TODOS" en su
        nombre.

        - En esta función, primero se cargan todas las leyes a un DataFrame. Luego, se filtran
        sus columnas por las columnas útiles (además, entre archivos tienen distintas cantidades
        de columnas). Finalmente, se concatenan entre sí a lo largo.
        '''

        print(f'{"SE ESTÁN CARGANDO LAS LEYES":^40}')
        nombres_leyes = [os.path.join('input', nombre) \
                        for nombre in os.listdir('input') if 'TODOS' in nombre]

        leyes_crudas = map(lambda x: pd.read_excel(x, header = 2), nombres_leyes)

        columnas_contrato = ['RUT-DV', 'NOMBRE', 'UNIDAD', 'CARGO', 'TOTAL HABER']

        leyes_columnas_utiles = list(map(lambda x: x[columnas_contrato], leyes_crudas))
        leyes_juntas = pd.concat(leyes_columnas_utiles)

        return leyes_juntas

    def cargar_honorarios(self):
        '''
        Esta función carga el archivo de funcionarios que trabajan por honorarios.

        - Se agrega la columna RUT-DV, ya que esta ausente en el archivo original
        - Se cambian los nombres de las columnas para que tengan el mismo nombre que las columnas
        de leyes.
        '''

        print(f'{"SE ESTÁN CARGANDO LOS HONORARIOS":^40}')
        nombre_archivo_honorarios = [nom for nom in os.listdir('input') if 'PERC' in nom][0]
        nombre_archivo_honorarios = os.path.join('input', nombre_archivo_honorarios)
        honorarios = pd.read_excel(nombre_archivo_honorarios)

        honorarios['RUT-DV'] = honorarios['RUT'].astype(str) + '-' + honorarios['DV'].astype(str)
        columnas_honorario = ['RUT-DV', 'NOMBRE', 'UNIDAD O SERVICIO DONDE SE DESEMPEÑA',
                              'CARGO', 'VALOR TOTAL O BRUTO']

        honorarios = honorarios[columnas_honorario].rename(
                                columns = {'UNIDAD O SERVICIO DONDE SE DESEMPEÑA': 'UNIDAD',
                                            'VALOR TOTAL O BRUTO': 'TOTAL HABER'})
        return honorarios

    def unificar_formatos(self, *args):
        '''
        Esta función es un pasador para aplicar la funcion self.formatear_df() a los argumentos
        de la función.
        '''

        lista_dfs_formateadas = list(map(self.formatear_df, args))
        return lista_dfs_formateadas

    def formatear_df(self, df_funcionarios):
        '''
        Esta función unifica las columnas "NOMBRE" y "RUT-DV" de la DataFrame que le llegue.
        Además, pone a la columna RUT-DV como índice.
        '''

        df_funcionarios['NOMBRE'] = df_funcionarios['NOMBRE'].str.strip().str.upper()
        df_funcionarios['RUT-DV'] = df_funcionarios['RUT-DV'].str.strip().str.upper()

        df_funcionarios = df_funcionarios.set_index('RUT-DV')

        return df_funcionarios

############################################################################################
    def agrupar_dfs(self, df_leyes_juntas, honorarios, tipo_agrupacion):
        print(f"{'ANALIZANDO LEYES':-^40}")
        suma_leyes_por_tipo_agrupacion = consolidar_informacion_dfs(df_leyes_juntas, tipo_agrupacion,
                                                                    False)
        suma_leyes_por_tipo_agrupacion['TIPO_CONTRATA'] = '1'

        print(f"{'ANALIZANDO HONORARIOS':-^40}")
        suma_honorarios_por_tipo_agrupacion = consolidar_informacion_dfs(honorarios, tipo_agrupacion,
                                                                        False)
        suma_honorarios_por_tipo_agrupacion['TIPO_CONTRATA'] = '2'

        print(f"{'ANALIZANDO LEYES Y HONORARIOS JUNTOS':-^40}")
        juntos_por_tipo_agrupacion = pd.concat([suma_leyes_por_tipo_agrupacion,
                                                    suma_honorarios_por_tipo_agrupacion])

        juntos_por_tipo_agrupacion = formatear_df(juntos_por_tipo_agrupacion)

        suma_juntos_por_tipo_agrupacion = consolidar_informacion_dfs(juntos_por_tipo_agrupacion,
                                                                    tipo_agrupacion, True)

        print(f"{'RESUMEN':-^40}")
        print(f'Hay {suma_leyes_por_tipo_agrupacion.shape[0]} funcionarios por Ley')
        print(f'Hay {suma_honorarios_por_tipo_agrupacion.shape[0]} funcionarios por Honorarios')
        print(f'Todos los funcionarios juntos suman {juntos_por_tipo_agrupacion.shape[0]} juntos')
        print(f'Al consolidar todos los campos, quedaron'
            f' {suma_juntos_por_tipo_agrupacion.shape[0]} funcionarios')

        suma_juntos_por_tipo_agrupacion.to_excel(f'por_{tipo_agrupacion}.xlsx')
        return suma_juntos_por_tipo_agrupacion

    def consolidar_informacion_dfs(self, df, consolidar_por, consolidar_contratos):
        if consolidar_por == 'funcionario':
            df = cambiar_redundancias(df, 'NOMBRE')
            df = cambiar_redundancias(df, 'CARGO')

            if consolidar_contratos:
                df = cambiar_redundancias(df, 'TIPO_CONTRATA')
                df_suma = df.groupby(by = ['RUT-DV', 'NOMBRE', 'CARGO', 'TIPO_CONTRATA']).sum() \
                                                                                     .reset_index()
            else:
                df_suma = df.groupby(by = ['RUT-DV', 'NOMBRE', 'CARGO']).sum().reset_index()

            return df_suma

        elif consolidar_por == 'unidad':
            df = cambiar_redundancias(df, 'NOMBRE')
            df = cambiar_redundancias(df, 'CARGO')
            df = cambiar_redundancias(df, 'UNIDAD')

            if consolidar_contratos:
                df = cambiar_redundancias(df, 'TIPO_CONTRATA')
                df_suma = df.groupby(by = ['RUT-DV', 'NOMBRE', 'CARGO', 'TIPO_CONTRATA','UNIDAD']).sum().reset_index()

            else:
                df_suma = df.groupby(by = ['RUT-DV', 'NOMBRE', 'CARGO', 'UNIDAD']).sum().reset_index()

            return df_suma


    def identificar_redundancias(self, df, caracteristica_a_identificar):
        agrupar_por = ['RUT-DV'] + caracteristica_a_identificar
        agrupado = df.groupby(by = agrupar_por).sum()
        duplicados = agrupado[agrupado.index.get_level_values(0).duplicated(keep = False)]
        duplicados_ordenados = duplicados.reset_index().sort_values(by = ['RUT-DV', 'TOTAL HABER'],
                                                                    ascending = False)
        return duplicados_ordenados

    def hacer_cambiador_de_caracteristica_redundante(self, df_con_duplicados, caracteristica):
        a_dejar = df_con_duplicados.iloc[::2]
        if caracteristica == 'CONTRATO':
            contratos_1 = ['1' for _ in range(a_dejar.shape[0])]
            diccionario = dict(zip(a_dejar['RUT-DV'], contratos_1))

        else:
            diccionario = dict(zip(a_dejar['RUT-DV'], a_dejar[caracteristica]))

        return diccionario

    def cambiar_redundancias(self, df, caracteristica_a_cambiar):
        df_con_redundancias = identificar_redundancias(df, [caracteristica_a_cambiar])
        print(f'\nEstos son los "{caracteristica_a_cambiar}" redundantes: \n'
            f'{df_con_redundancias.to_markdown()}\n')

        dict_cambiador = hacer_cambiador_de_caracteristica_redundante(df_con_redundancias, 
                                                                    caracteristica_a_cambiar)

        # print(f'\nLos ruts quedarán de la siguiente forma:\n'
        #       f'{json.dumps(dict_cambiador, indent = 1)}\n')

        for rut, caracteristica in dict_cambiador.items():
            df.loc[rut, caracteristica_a_cambiar] = caracteristica

        return df

    def guardar_archivos(self, suma_por_funcionario, suma_por_unidad):
        with pd.ExcelWriter('output.xlsx') as writer:
            suma_por_funcionario.to_excel(writer, index = False, sheet_name = 'suma_por_funcionario')
            suma_por_unidad.to_excel(writer, index = False, sheet_name = 'suma_por_unidad')

modulo_rrhh_sigcom = ModuloRecursosHumanosSIGCOM()
modulo_rrhh_sigcom.correr_programa()
