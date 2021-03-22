import os
from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required
from pymongo import MongoClient
import logging
import json
import re
import spacy
#import pt_core_news_sm
import pt_core_news_lg
import unicodedata
import re
#import nltk
#nltk.download('wordnet')
#from nltk.stem import WordNetLemmatizer

# path /chatbot/question?code_user=xxxx&code_before=xxxxxx&input=xxxxxx
path_params = reqparse.RequestParser()
path_params.add_argument('code_user', type=int)
path_params.add_argument('code_relation', type=int)
path_params.add_argument('code_before', type=int)
path_params.add_argument('input', type=str)

#python -m spacy download pt_core_news_lg
#nlp = spacy.load('pt_core_news_sm')
#nlp = spacy.load('pt_core_news_md')
nlp = spacy.load('pt_core_news_lg')

class Chatbot(Resource):

    def get(self):

        #recupera os parametros da requisicao.
        dados = path_params.parse_args()

        MONGO_DB_URL = str(os.environ.get("MONGO_DB_URL", "localhost"))
        MONGO_DB_PORTA = int(os.environ.get("MONGO_DB_PORTA", 27017))

        #conexão local padrão
        #cliente = MongoClient('mongodb://localhost:27017/')
        #cliente = MongoClient('localhost', 27017)
        cliente = MongoClient(MONGO_DB_URL, MONGO_DB_PORTA)

        #banco chatbotsdb
        db = cliente.chatbotsdb
        #coleção chatbot
        botQuestions = db.chatbot

        #rgxFiltroInput = re.compile('.*' + dados['input'] + '.*', re.IGNORECASE)  # compile the regex

        #busca a pergunta/resposata com base no input do usuário.
        if(dados['code_relation']):
            questionData = botQuestions.find({"code_user": dados['code_user'], "code_relation": dados['code_relation']})
            logging.warning('code_relation: ' + json.dumps(dados['code_relation']))
            if(questionData is None):
                questionData = botQuestions.find({"code_user": dados['code_user'], "code_relation": 0})
                logging.warning('Entrou aqui!')
            else:
                logging.warning('questionData is not None!')
        else:
            questionData = botQuestions.find({"code_user": dados['code_user'], "code_relation": 0})
            logging.warning('Nao veio code_relation!')

        #Filtrando através da question do usuário, aqui deve ser utilizado o SpaCy NLP:
        #questionData = [item for item in questionData if dados['input'] in item['input']]

        # modelo JSON: registro--> {campo1:'valor'; campo2:'valor'}.
        lista = [{campo: registro[campo] for campo in registro if campo != '_id'} for registro in questionData]

        lista = [{campo: str(registro[campo]) for campo in registro if campo != '_id'} for registro in lista]

        entrada = nlp(json.loads(json.dumps(removerAcentosECaracteresEspeciais(dados['input']))))

        for item in lista:
            item_comparar = nlp(json.loads(json.dumps(removerAcentosECaracteresEspeciais(item['input']))))
            logging.warning("entrada: {} item: {} similaridade: {} %.".format(entrada, item_comparar, item_comparar.similarity(entrada)))

        logging.warning('code_user: ' + json.dumps(dados['code_user']))
        logging.warning('input: ' + json.loads(json.dumps(removerAcentosECaracteresEspeciais(dados['input']))))

        #Remove Pontuação

        #Normalizar vocabulário

        #Extrair Lema

        #Filtrando pela similaridade
        lista = filtrarSimilaridade(entrada, lista, 0.7)

        # return bson.json_util.dumps(questionData)

        #lista = [{item: data[item]} for item in lista if item.input.constains(dados['input'])  for data in lista]
        #lista = [{item: data[item]} for item in lista if(dados['input'] in item.input)]

        logging.warning('Retorno:')
        logging.warning(json.loads(json.dumps(lista)))

        if(questionData):
            return json.loads(json.dumps(lista)), 200
            # return json.dumps(questionData, default=json_util.default), 200 # Http Status Code 200 Sucesso.
        else:
            return None, 404 # Http Status Code 404 Não Encontrado.


def filtrarSimilaridade(entrada, lista, fatorSimilaridade):
    lista = [item for item in lista if nlp(json.loads(json.dumps(removerAcentosECaracteresEspeciais(item['input'])))).similarity(entrada) > fatorSimilaridade]
    return lista


"""
https://gist.github.com/boniattirodrigo/67429ada53b7337d2e79
A remoção de acentos foi baseada em uma resposta no Stack Overflow.
http://stackoverflow.com/a/517974/3464573
https://minerandodados.com.br/mineracao-de-textos-7-tecnicas/
"""

def removerAcentosECaracteresEspeciais(texto):
    # Tipos de Normalização NFD e NFKD
    # --> https://qastack.com.br/programming/7931204/what-is-normalized-utf-8-all-about
    # --> https://www.otaviomiranda.com.br/2020/normalizacao-unicode-em-python/
    # Unicode normalize transforma um caracter em seu equivalente em latin.
    # nfkd = unicodedata.normalize('NFKD', texto)
    texto = normalizarTexto(texto)

    textoSemAcento = u"".join([caracter for caracter in texto if not unicodedata.combining(caracter)])

    # remove punctuation tokens that are in the word string like 'bye!' -> 'bye'
    #REPLACE_PUNCT = re.compile("(\.)|(\;)|(\:)|(\!)|(\')|(\?)|(\,)|(\")|(\()|(\))|(\[)|(\])")

    # Usa expressão regular para retornar a palavra apenas com números, letras e espaço
    #return re.sub('[^a-zA-Z0-9 \\\]', '', palavraSemAcento)
    textoSemAcento = re.sub("(\.)|(\;)|(\:)|(\!)|(\')|(\?)|(\,)|(\")|(\()|(\))|(\[)|(\])", '', textoSemAcento)

    #textoSemAcento = lematizarTexto(textoSemAcento)

    textoSemAcento = removerStopWords(textoSemAcento)

    #textoSemAcento = removerPontuacao(textoSemAcento)

    #textoSemAcento = filtrarAlfabetico(textoSemAcento)

    return textoSemAcento


def normalizarTexto(texto):
    # Tipos de Normalização NFD e NFKD
    # --> https://qastack.com.br/programming/7931204/what-is-normalized-utf-8-all-about
    # --> https://www.otaviomiranda.com.br/2020/normalizacao-unicode-em-python/
    # Unicode normalize transforma um caracter em seu equivalente em latin.
    # nfkd = unicodedata.normalize('NFKD', texto)

    texto = unicodedata.normalize('NFD', texto)

    texto = texto .lower()

    return texto


def lematizarTexto(texto):
    #doc = nlp(texto)
    #texto = u" ".join([token.lemma_ for token in doc])
    #return texto
    lematizador = WordNetLemmatizer()
    texto = lematizador.lemmatize(texto)
    return texto

"""
https://stackabuse.com/removing-stop-words-from-strings-in-python/
https://demacdolincoln.github.io/anotacoes-nlp/posts/pre-processamento-de-textos/
http://python.w3.pt/?p=234
https://gist.github.com/alopes/5358189
"""
def removerStopWords(texto):
    texto = normalizarTexto(texto)
    """stopwords = [ 'a', 'à', 'adeus', 'agora', 'aí', 'ainda', 'além', 'algo', 'alguém', 'algum', 'alguma', 'algumas', 'alguns', 'ali', 'ampla', 'amplas', 'amplo', 'amplos', 'ano', 'anos', 'ante', 'antes', 'ao', 'aos', 'apenas', 'apoio', 'após', 'aquela', 'aquelas', 'aquele', 'aqueles', 'aqui', 'aquilo', 'área', 'as', 'às', 'assim', 'até', 'atrás', 'através', 'baixo', 'bastante', 'bem', 'boa', 'boas', 'bom', 'bons', 'breve', 'cá', 'cada', 'catorze', 'cedo', 'cento', 'certamente', 'certeza', 'cima', 'cinco', 'coisa', 'coisas', 'com', 'como', 'conselho', 'contra', 'contudo', 'custa', 'da', 'dá', 'dão', 'daquela', 'daquelas', 'daquele', 'daqueles', 'dar', 'das', 'de', 'debaixo', 'dela', 'delas', 'dele', 'deles', 'demais', 'dentro', 'depois', 'desde', 'dessa', 'dessas', 'desse', 'desses', 'desta', 'destas', 'deste', 'destes', 'deve', 'devem', 'devendo', 'dever', 'deverá', 'deverão', 'deveria', 'deveriam', 'devia', 'deviam', 'dez', 'dezanove', 'dezasseis', 'dezassete', 'dezoito', 'dia', 'diante', 'disse', 'disso', 'disto', 'dito', 'diz', 'dizem', 'dizer', 'do', 'dois', 'dos', 'doze', 'duas', 'dúvida', 'e', 'é', 'ela', 'elas', 'ele', 'eles', 'em', 'embora', 'enquanto', 'entre', 'era', 'eram', 'éramos', 'és', 'essa', 'essas', 'esse', 'esses', 'esta', 'está', 'estamos', 'estão', 'estar', 'estas', 'estás', 'estava', 'estavam', 'estávamos', 'este', 'esteja', 'estejam', 'estejamos', 'estes', 'esteve', 'estive', 'estivemos', 'estiver', 'estivera', 'estiveram', 'estivéramos', 'estiverem', 'estivermos', 'estivesse', 'estivessem', 'estivéssemos', 'estiveste', 'estivestes', 'estou', 'etc', 'eu', 'exemplo', 'faço', 'falta', 'favor', 'faz', 'fazeis', 'fazem', 'fazemos', 'fazendo', 'fazer', 'fazes', 'feita', 'feitas', 'feito', 'feitos', 'fez', 'fim', 'final', 'foi', 'fomos', 'for', 'fora', 'foram', 'fôramos', 'forem', 'forma', 'formos', 'fosse', 'fossem', 'fôssemos', 'foste', 'fostes', 'fui', 'geral', 'grande', 'grandes', 'grupo', 'há', 'haja', 'hajam', 'hajamos', 'hão', 'havemos', 'havia', 'hei', 'hoje', 'hora', 'horas', 'houve', 'houvemos', 'houver', 'houvera', 'houverá', 'houveram', 'houvéramos', 'houverão', 'houverei', 'houverem', 'houveremos', 'houveria', 'houveriam', 'houveríamos', 'houvermos', 'houvesse', 'houvessem', 'houvéssemos', 'isso', 'isto', 'já', 'la', 'lá', 'lado', 'lhe', 'lhes', 'lo', 'local', 'logo', 'longe', 'lugar', 'maior', 'maioria', 'mais', 'mal', 'mas', 'máximo', 'me', 'meio', 'menor', 'menos', 'mês', 'meses', 'mesma', 'mesmas', 'mesmo', 'mesmos', 'meu', 'meus', 'mil', 'minha', 'minhas', 'momento', 'muita', 'muitas', 'muito', 'muitos', 'na', 'nada', 'não', 'naquela', 'naquelas', 'naquele', 'naqueles', 'nas', 'nem', 'nenhum', 'nenhuma', 'nessa', 'nessas', 'nesse', 'nesses', 'nesta', 'nestas', 'neste', 'nestes', 'ninguém', 'nível', 'no', 'noite', 'nome', 'nos', 'nós', 'nossa', 'nossas', 'nosso', 'nossos', 'nova', 'novas', 'nove', 'novo', 'novos', 'num', 'numa', 'número', 'nunca', 'o', 'obra', 'obrigada', 'obrigado', 'oitava', 'oitavo', 'oito', 'onde', 'ontem', 'onze', 'os', 'ou', 'outra', 'outras', 'outro', 'outros', 'para', 'parece', 'parte', 'partir', 'paucas', 'pela', 'pelas', 'pelo', 'pelos', 'pequena', 'pequenas', 'pequeno', 'pequenos', 'per', 'perante', 'perto', 'pode', 'pude', 'pôde', 'podem', 'podendo', 'poder', 'poderia', 'poderiam', 'podia', 'podiam', 'põe', 'põem', 'pois', 'ponto', 'pontos', 'por', 'porém', 'porque', 'porquê', 'posição', 'possível', 'possivelmente', 'posso', 'pouca', 'poucas', 'pouco', 'poucos', 'primeira', 'primeiras', 'primeiro', 'primeiros', 'própria', 'próprias', 'próprio', 'próprios', 'próxima', 'próximas', 'próximo', 'próximos', 'pude', 'puderam', 'quais', 'quáis', 'qual', 'quando', 'quanto', 'quantos', 'quarta', 'quarto', 'quatro', 'que', 'quê', 'quem', 'quer', 'quereis', 'querem', 'queremas', 'queres', 'quero', 'questão', 'quinta', 'quinto', 'quinze', 'relação', 'sabe', 'sabem', 'são', 'se', 'segunda', 'segundo', 'sei', 'seis', 'seja', 'sejam', 'sejamos', 'sem', 'sempre', 'sendo', 'ser', 'será', 'serão', 'serei', 'seremos', 'seria', 'seriam', 'seríamos', 'sete', 'sétima', 'sétimo', 'seu', 'seus', 'sexta', 'sexto', 'si', 'sido', 'sim', 'sistema', 'só', 'sob', 'sobre', 'sois', 'somos', 'sou', 'sua', 'suas', 'tal', 'talvez', 'também', 'tampouco', 'tanta', 'tantas', 'tanto', 'tão', 'tarde', 'te', 'tem', 'tém', 'têm', 'temos', 'tendes', 'tendo', 'tenha', 'tenham', 'tenhamos', 'tenho', 'tens', 'ter', 'terá', 'terão', 'terceira', 'terceiro', 'terei', 'teremos', 'teria', 'teriam', 'teríamos', 'teu', 'teus', 'teve', 'ti', 'tido', 'tinha', 'tinham', 'tínhamos', 'tive', 'tivemos', 'tiver', 'tivera', 'tiveram', 'tivéramos', 'tiverem', 'tivermos', 'tivesse', 'tivessem', 'tivéssemos', 'tiveste', 'tivestes', 'toda', 'todas', 'todavia', 'todo', 'todos', 'trabalho', 'três', 'treze', 'tu', 'tua', 'tuas', 'tudo', 'última', 'últimas', 'último', 'últimos', 'um', 'uma', 'umas', 'uns', 'vai', 'vais', 'vão', 'vários', 'vem', 'vêm', 'vendo', 'vens', 'ver', 'vez', 'vezes', 'viagem', 'vindo', 'vinte', 'vir', 'você', 'vocês', 'vos', 'vós', 'vossa', 'vossas', 'vosso', 'vossos', 'zero', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '_' ]
    """
    #doc = nlp(texto)
    #texto = u" ".join([str(token) for token in doc if token.is_stop])
    #return texto
    stopwords = [ 'a', 'o', 'à', 'e', 'é', 'me', 'fale', 'quero', 'saber', 'sobre', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '_']
    palavras = [i for i in texto.split() if not i in stopwords]
    return (" ".join(palavras))



def removerPontuacao(texto):
    doc = nlp(texto)
    texto = u" ".join([str(token) for token in doc if token.is_punct])
    return texto

def filtrarAlfabetico(texto):
    doc = nlp(texto)
    texto = u" ".join([str(token) for token in doc if token.is_alpha])
    return texto
