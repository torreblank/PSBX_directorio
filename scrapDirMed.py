# -*- coding: utf-8 -*-
"""
Created on Mon Jul/ 2023
Obtener datos del directorio médico público
@author: https://github.com/torreblank
"""
from   bs4 import BeautifulSoup
import datetime as dt
import re
import requests

cleanStr = lambda s : s.replace(f'\t','').replace('\r\n','').replace(f'\xa0','').replace('&amp;#034;','')

def getOpciones(lista:str, soup) :
  menu = soup.find('td',string=lista)
  arr={}
  for opcion in menu.find_next_sibling().find_all('option'):
    i = int(opcion.attrs["value"])
    if i>=0:
      arr.setdefault(i,cleanStr(opcion.string))
  return arr

def getWebPage(pag=0, servicio=-1, especialidad=-1, estado=-1) :
  sitio = "https://comunidad.banxico.org.mx"
  URL = f"{sitio}/CatPrestadoresWA/buscarPrestadorAct.do?BMXC_busquedaAvanzada=false&BMXC_nombre=&BMXC_pagina={pag}&BMXC_colonia="+\
        f"&BMXC_servicio={servicio}&BMXC_estado={estado}&BMXC_especialidad={especialidad}&BMXC_planMedico=-1&BMXC_capturado=true&BMXC_municipio="
  return BeautifulSoup(requests.get(URL).text, "html.parser") #, from_encoding='ISO-8859-1')

soup    = getWebPage(0, 2)
edoDic  = getOpciones('Estado'      ,soup)
espDic  = getOpciones('Especialidad',soup)
servDic = getOpciones('Servicio'    ,soup)
del soup

def getPags(soup) :
  pags = []
  try:
    for _ in soup.find('td', class_='text rowodd').find_all('a') :
      if _.string.replace(f'\xa0','').isdecimal() :
        pags.append(int(_.string)-1)
  except: 
      pass
  return pags

def getTelPlan(ubicacion) :
  tablas = None
  for sup in ubicacion.parents:
    if sup.table is not None:
      tablas = sup
      break
  tablas = tablas.find_all('tr', class_='titulos_tabla', string=re.compile('Teléfono|Planes M'))
  texto  = ''
  for tabla in tablas:
    rows = tabla.parent.find_all('tr', class_=['text even','text odd'])
    texto= f'{texto}{tabla.td.string}: '
    for data in rows :
      try :
        if data.td.string == 'Básico' :
          texto = f'{texto}Todos'
          break
        else :
          texto = f'{texto}[{data.td.string}]'
      except:
        pass
    texto = f'{texto}_'
  return texto.replace(f'\xa0','')

def addData(dic, prestador, ubicacion) :
  llave,dato = prestador.tr.string,''
  try:
    dato = cleanStr(ubicacion.string)
    try:
      dato = f'{dato}_{getTelPlan(ubicacion)}'
    except:
      pass
  except:
    pass
  if dato != '':
    try:
      dic[llave].append(dato)
    except:
      dic.setdefault(llave,[dato]) 

def dataPrestador(dic, soup) :
  prestadores = soup.find_all('table', style='width:100%;') 
  for prestador in prestadores :
    for ubicacion in prestador.find_all('td', string=re.compile('C\.P\.\d')) :
      addData(dic, prestador, ubicacion)
    # los textos TD no son vistos si están junto a un anchor A
    # el siguiente loop lee las ubicaciones en esos casos
    for anchor in prestador.find_all('a') :
      ubicacion = anchor.previous_element
      addData(dic, prestador, ubicacion)

def splitTelPlan(k,d) :
  tmp  = d.split(sep='_', maxsplit=2)
  plan, tels = '',''
  try:
    plan = tmp[1].split(sep=':')[1]
  except:
    pass
  try:
    tels = tmp[2].split(sep=':')[1].replace('_','')
  except:
    pass
  return f'{tmp[0]}\t{plan}\t{tels}'

def scrapEspecialidad():
  print(f'Inicio: {dt.datetime.now()}\n<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>')
  with open('especialidad.csv','w') as f:
    f.write(f'SERVICIO\tPRESTADOR\tUBICACIÓN\tPLAN\tTELS\n')
    for espec in espDic : 
      dic = {}
      soup = getWebPage(0, servicio=-1, especialidad=espec)
      for pag in getPags(soup) :
        print(f'Servicio: {espDic[espec]} | Hoja: {pag+1}')
        soup = getWebPage(pag, servicio=1, especialidad=espec) if (pag>0) else soup
        dataPrestador(dic, soup)
      for k in dic.keys():
        for d in dic[k]:
          f.write(f'{espDic[espec].lstrip()}\t{k}\t{splitTelPlan(k,d)}\n')
  print(f'Fin: {dt.datetime.now()}\n<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>')

def scrapServicio():
  print(f'Inicio: {dt.datetime.now()}\n<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>')
  with open('servicios.csv','w') as f:
    f.write(f'SERVICIO\tPRESTADOR\tUBICACIÓN\tPLAN\tTELS\n')
    for servicio in list(range(2,12))+list(range(15,19)) : 
      dic = {}
      soup = getWebPage(0, servicio)
      for pag in getPags(soup) :
        print(f'Servicio: {servDic[servicio]} | Hoja: {pag+1}')
        soup = getWebPage(pag, servicio) if (pag>0) else soup
        dataPrestador(dic, soup)
      for k in dic.keys():
        for d in dic[k]:
          f.write(f'{servDic[servicio]}\t{k}\t{splitTelPlan(k,d)}\n')
  print(f'Fin: {dt.datetime.now()}\n<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>')

###########################################
if __name__ == "__main__":
  scrapEspecialidad()
  scrapServicio()
