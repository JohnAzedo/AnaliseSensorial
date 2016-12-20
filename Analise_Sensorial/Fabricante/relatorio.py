 # Create your views here.
import csv
#from reportlab.pdfgen import canvas
from io import BytesIO
#from reportlab.lib.pagesizes import letter, A4
#from random import randint
#from io import StringIO
from Fabricante.metodos import transcricao_numero_letra
from django.http import HttpResponse
from Fabricante.models import *
from django.shortcuts import redirect, get_object_or_404

#Relatorio
import time
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

#Gráficos
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing, Rect, String, Group, Line
from reportlab.graphics.widgets.markers import makeMarker
from reportlab.lib import colors

def put_string(dictionary):
	label = ''
	if dictionary['type'] == 'negrito':
		label = '<font size=%s><b>%s</b></font>' % (dictionary['size'], dictionary['text'])
	else:
		label = '<font size=%s>%s</font>' % (dictionary['size'], dictionary['text'])

	dictionary['elements'].append(Paragraph(label, dictionary['styles'][dictionary['style']]))
	dictionary['elements'].append(Spacer(1, dictionary['spacer']))


def porcentagem(number, number_total):
	porcento = (number/number_total) * 100
	return porcento

#Método certo
def relatorio_final(request, id):
	analise = get_object_or_404(AnaliseSensorial, id=id)
	response = HttpResponse(content_type='application/pdf')
	response['Content-Disposition'] = 'attachment; filename="relatorio.pdf"'

	#Iniciando variáveis importantes
	buff = BytesIO()

	#Criando arquivos com as dimensões de margem
	arquivo = SimpleDocTemplate(buff, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=18)
	elements = []

	styles = getSampleStyleSheet()
	styles.add(ParagraphStyle(name='centered', alignment=TA_JUSTIFY))
	styles.add(ParagraphStyle(name='body', alignment=TA_JUSTIFY, fontSize=10))

	#Iniciando um dicionário de dados sobre o pdf
	dictionary = {'analise':analise, 'elements':elements, 'styles':styles}

	#Renderizando o título do documento
	dictionary['size'] = '20'
	dictionary['text'] = 'Relatório sobre a analise sensorial: ' + str(analise.nome)
	dictionary['style'] = 'title'
	dictionary['spacer'] = 20
	dictionary['type'] = 'normal'
	put_string(dictionary)
	#----------------------------------------------------------------------------------

	#Renderizando informações sobre a análise
	dictionary['size'] = '14'
	dictionary['spacer'] = 12
	dictionary['style'] = 'BodyText'
	dictionary['type'] = 'normal'

	dictionary['text'] = 'Nome: ' + str(analise.nome)
	put_string(dictionary)

	dictionary['text'] = 'Descrição: ' + str(analise.descricao)
	put_string(dictionary)

	dictionary['text'] = 'Quantidade de provadores: ' + str(analise.quantidade_pessoas)
	put_string(dictionary)

	dictionary['text'] = 'Quantidade de amostras: ' + str(analise.quantidade_amostras)
	put_string(dictionary)

	dictionary['text'] = 'Fabricante: ' + str(analise.user.first_name)
	put_string(dictionary)
	#-----------------------------------------------------------------------------------

	#Recebendo perguntas
	perguntas = Pergunta.objects.filter(analise_id = analise.id)

	#Renderizar as perguntas
	dictionary['elements'].append(Spacer(1, 24))
	dictionary['type'] = 'negrito'

	for pergunta in perguntas:
		dictionary['text'] = pergunta.pergunta
		dictionary['size'] = '18'
		dictionary['type'] = 'negrito'
		put_string(dictionary)

		for index in range(analise.quantidade_amostras):
			dictionary['text'] = 'Amostra %s' % transcricao_numero_letra(index)
			dictionary['type'] = 'Normal'
			dictionary['size'] = '14'
			put_string(dictionary)

			grafico = Drawing(400, 150)
			cartoon = VerticalBarChart()

			#Colocar tamanho do gráfico
			cartoon.height = 125
			cartoon.width = 500

			#Colocando os dados no gráfico
			cartoon.strokeColor = colors.black

			#Aplicando valores maximos e minimos para o gráfico
			cartoon.valueAxis.valueMin = 0
			cartoon.valueAxis.valueMax = analise.quantidade_pessoas#Aqui ficará a 'quantidade_pessoas'
			cartoon.valueAxis.valueStep = (analise.quantidade_pessoas/10)

			#Arrumando as labels do gráfico
			cartoon.categoryAxis.labels.boxAnchor = 'ne'
			cartoon.categoryAxis.labels.dx = 10

			#Aqui ficará a divisão
			if pergunta.tipo == 'PSN':
				respostas = Boolean.objects.filter(
					analise_id = id,
					pergunta_id=pergunta.id,
					amostra__tipo=transcricao_numero_letra(index)
				)

				contador_true = 0
				contador_false = 0

				for resposta in respostas:
					if resposta.resposta == True:
						contador_true += 1
					else:
						contador_false += 1

				#Caracterizando o grafico de acordo
				data = [(contador_true, contador_false),]
				cartoon.data = data
				cartoon.categoryAxis.categoryNames = ['Sim', 'Não']
				cartoon.bars[(0,0)].fillColor = colors.green
				cartoon.bars[(0,1)].fillColor = colors.red

				grafico.add(cartoon)
				elements.append(grafico)
				elements.append(Spacer(1,20))

				porcentagem_sim = porcentagem(contador_true, analise.quantidade_pessoas)
				porcentagem_nao = porcentagem(contador_false, analise.quantidade_pessoas)
				dictionary['text'] = """Nessa questão {por_sim:.2f}{symbol} dos
				provadores responderam SIM - {n} pessoa(s)
				-  e {por_nao:.2f}{symbol} responderam
				NÃO - {n2} pessoa(s).""" .format(symbol="%", por_sim=(porcentagem_sim), n=contador_true,
				por_nao=porcentagem_nao, n2=contador_false)

				dictionary['type'] = "Normal"
				dictionary['size'] = "12"
				put_string(dictionary)

				elements.append(Spacer(1,20))

			elif pergunta.tipo == 'PHD':
				respostas = Hedonica.objects.filter(
					analise_id=id,
					pergunta_id=pergunta.id,
					amostra__tipo=transcricao_numero_letra(index)
				)

				#Variáveis
				h_01 = 0
				h_02 = 0
				h_03 = 0
				h_04 = 0
				h_05 = 0
				h_06 = 0
				h_07 = 0
				h_08 = 0
				h_09 = 0

				for resposta in respostas:
					if resposta.resposta == 1:
						h_01 += 1
					elif resposta.resposta == 2:
						h_02 += 1
					elif resposta.resposta == 3:
						h_03 += 1
					elif resposta.resposta == 4:
						h_04 += 1
					elif resposta.resposta == 5:
						h_05 += 1
					elif resposta.resposta == 6:
						h_06 += 1
					elif resposta.resposta == 7:
						h_07 += 1
					elif resposta.resposta == 8:
						h_08 += 1
					else:
						h_09 += 1


				data = [(h_01, h_02, h_03, h_04, h_05, h_06, h_07, h_08, h_09,)]
				cartoon.data = data
				cartoon.categoryAxis.categoryNames = [
					'Desgostei extremamente',
					'Desgostei muito',
					'Desgostei moderadamente',
					'Desgostei ligeiramente',
					'Nem gostei / Nem desgostei',
					'Gostei ligeiramente',
					'Gostei moderadamente',
					'Gostei muito',
					'Gostei muitíssimo'
				]

				cartoon.bars[(0,0)].fillColor = colors.green
				cartoon.bars[(0,1)].fillColor = colors.red
				cartoon.bars[(0,2)].fillColor = colors.yellow
				cartoon.bars[(0,3)].fillColor = colors.blue
				cartoon.bars[(0,4)].fillColor = colors.pink
				cartoon.bars[(0,5)].fillColor = colors.gray
				cartoon.bars[(0,6)].fillColor = colors.purple
				cartoon.bars[(0,7)].fillColor = colors.black
				cartoon.bars[(0,8)].fillColor = colors.orange

				cartoon.categoryAxis.labels.dx = 8
				cartoon.categoryAxis.labels.dy = -2
				cartoon.categoryAxis.labels.angle = 30

				grafico.add(cartoon)
				elements.append(grafico)
				elements.append(Spacer(1,60))

				#Variável de menor nome
				q_p = analise.quantidade_pessoas

				dictionary['text'] = """Resultados:
				*{p_01}{symbol} - {n_01} pessoa(s) - responderam que <b>desgostaram extremamente</b> dessa amostra.\n
				*{p_02}{symbol} - {n_02} pessoa(s) - responderam que <b>desgostaram muito</b> dessa amostra.\n
				*{p_03}{symbol} - {n_03} pessoa(s) - responderam que <b>desgostaram moderadamente</b> dessa amostra.\n
				*{p_04}{symbol} - {n_04} pessoa(s) - responderam que <b>desgostaram ligeiramente</b> dessa amostra.\n
				*{p_05}{symbol} - {n_05} pessoa(s) - responderam que <b>nem gostaram, nem desgostaram</b> dessa amostra.\n
				*{p_06}{symbol} - {n_06} pessoa(s) - responderam que <b>gostaram ligeiramente</b>  dessa amostra.\n
				*{p_07}{symbol} - {n_07} pessoa(s) - responderam que <b>gostaram moderadamente</b> dessa amostra.\n
				> {p_08}{symbol} - {n_08} pessoa(s) - responderam que <b>gostaram muito</b> dessa amostra.\n
				> {p_09}{symbol} - {n_09} pessoa(s) - responderam que <b>gostaram extremamente</b> dessa amostra.\n
				""".format(symbol="%",

				#Porcentagens de concatenação de string
				p_01=porcentagem(h_01, q_p), p_02=porcentagem(h_02, q_p),
				p_03=porcentagem(h_03, q_p), p_04=porcentagem(h_04, q_p),
				p_05=porcentagem(h_05, q_p), p_06=porcentagem(h_06, q_p),
				p_07=porcentagem(h_07, q_p), p_08=porcentagem(h_08, q_p),
				p_09=porcentagem(h_09, q_p),

				#Número de pessoas
				n_01=h_01, n_02=h_02, n_03=h_03, n_04=h_04,
				n_05=h_05, n_06=h_06, n_07=h_07, n_08=h_08,
				n_09=h_09)
				dictionary['size'] = '12'
				dictionary['type'] = 'Normal'
				put_string(dictionary)
				elements.append(Spacer(1,30))
			elif pergunta.tipo == 'PDT':
				respostas = Dissertativa.objects.filter(
					analise_id=id,
					pergunta_id=pergunta.id,
					amostra__tipo=transcricao_numero_letra(index)
				)


			else:
				respostas = IntencaoCompra.objects.filter(
					analise_id=id,
					pergunta_id=pergunta.id,
					amostra__tipo=transcricao_numero_letra(index)
				)

				ic_01 = 0
				ic_02 = 0
				ic_03 = 0
				ic_04 = 0
				ic_05 = 0

				for resposta in respostas:
					if resposta.resposta == 1:
						ic_01 += 1
					elif resposta.resposta == 2:
						ic_02 += 1
					elif resposta.resposta == 3:
						ic_03 += 1
					elif resposta.resposta == 4:
						ic_04 += 1
					else:
						ic_05 += 1

				data = [(ic_01, ic_02, ic_03, ic_04, ic_05),]
				cartoon.data = data
				cartoon.categoryAxis.categoryNames = [
					'Certamente não compraria',
					'Possivelmente não compraria',
					'Talvez comprasse ou não comprasse',
					'Possivelmente compraria',
					'Certamente compraria'
				]

				cartoon.bars[(0,0)].fillColor = colors.green
				cartoon.bars[(0,1)].fillColor = colors.red
				cartoon.bars[(0,2)].fillColor = colors.yellow
				cartoon.bars[(0,3)].fillColor = colors.blue
				cartoon.bars[(0,4)].fillColor = colors.pink

				cartoon.categoryAxis.labels.dx = 8
				cartoon.categoryAxis.labels.dy = -2
				cartoon.categoryAxis.labels.angle = 30

				grafico.add(cartoon)
				elements.append(grafico)
				elements.append(Spacer(1,50))
	#-----------------------------------------------------------------------------------
	"""d = Drawing(400, 150)
	data = [
	        (13, 5),
	        ]
	bc = VerticalBarChart()
	bc.x = 60
	bc.height = 125
	bc.width = 400
	bc.data = data
	bc.strokeColor = colors.black
	bc.valueAxis.valueMin = 0
	bc.valueAxis.valueMax = 50
	bc.valueAxis.valueStep = 5  #Distancia entre pontos na linha y
	bc.categoryAxis.labels.boxAnchor = 'ne'
	bc.categoryAxis.labels.dx = 8
	bc.categoryAxis.labels.dy = -2
	bc.categoryAxis.labels.angle = 30
	bc.categoryAxis.categoryNames = ['Sim','Não',]
	#bc.categoryAxis.categoryNames['Sim'].Color = colors.green
	bc.groupSpacing = 10
	bc.barSpacing = 2
	#bc.categoryAxis.style = 'stacked'  # Una variación del gráfico
	d.add(bc)
	#pprint.pprint(bc.getProperties())
	elements.append(d)"""


	arquivo.build(elements)
	response.write(buff.getvalue())
	buff.close()
	return response
