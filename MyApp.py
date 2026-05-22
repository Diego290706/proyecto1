import sqlite3
import os
import hashlib
import time

os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.core.window import Window
from kivy.properties import NumericProperty, StringProperty, BooleanProperty
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout

Window.size = (360, 640)

# ══════════════════════════════════════════════
#  BASE DE DATOS
# ══════════════════════════════════════════════
def hash_pwd(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect('tequix_aprende.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios
                 (id INTEGER PRIMARY KEY, user TEXT UNIQUE, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS progreso
                 (user TEXT, course TEXT, passed INTEGER DEFAULT 0,
                  PRIMARY KEY (user, course))''')

    # ── Migración automática de la tabla logros ─────────────────────────
    # Si existe con columna 'logro' (versión vieja), la renombramos y
    # recreamos con 'logro_id' para no perder datos del usuario.
    c.execute("PRAGMA table_info(logros)")
    cols = [row[1] for row in c.fetchall()]
    if cols and 'logro_id' not in cols:
        # Tabla vieja existe con columna 'logro' → migrar
        c.execute("ALTER TABLE logros RENAME TO logros_old")
        c.execute('''CREATE TABLE logros
                     (user TEXT, logro_id TEXT,
                      PRIMARY KEY (user, logro_id))''')
        if 'logro' in cols:
            c.execute("INSERT OR IGNORE INTO logros (user, logro_id) SELECT user, logro FROM logros_old")
        c.execute("DROP TABLE logros_old")
    elif not cols:
        # Tabla no existe aún → crearla desde cero
        c.execute('''CREATE TABLE IF NOT EXISTS logros
                     (user TEXT, logro_id TEXT,
                      PRIMARY KEY (user, logro_id))''')
    # Si ya tiene logro_id no se hace nada
    # ───────────────────────────────────────────────────────────────────

    conn.commit()
    conn.close()

def user_exists(user):
    conn = sqlite3.connect('tequix_aprende.db')
    c = conn.cursor()
    c.execute("SELECT id FROM usuarios WHERE user=?", (user,))
    row = c.fetchone()
    conn.close()
    return row is not None

def check_login(user, pwd):
    conn = sqlite3.connect('tequix_aprende.db')
    c = conn.cursor()
    c.execute("SELECT id FROM usuarios WHERE user=? AND password=?", (user, hash_pwd(pwd)))
    row = c.fetchone()
    conn.close()
    return row is not None

def register_user_db(user, pwd):
    try:
        conn = sqlite3.connect('tequix_aprende.db')
        c = conn.cursor()
        c.execute("INSERT INTO usuarios (user, password) VALUES (?,?)", (user, hash_pwd(pwd)))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def get_progress(user, course):
    conn = sqlite3.connect('tequix_aprende.db')
    c = conn.cursor()
    c.execute("SELECT passed FROM progreso WHERE user=? AND course=?", (user, course))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def set_progress(user, course, passed):
    conn = sqlite3.connect('tequix_aprende.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO progreso (user, course, passed) VALUES (?,?,?)",
              (user, course, passed))
    conn.commit()
    conn.close()

def get_logros(user):
    conn = sqlite3.connect('tequix_aprende.db')
    c = conn.cursor()
    c.execute("SELECT logro_id FROM logros WHERE user=?", (user,))
    rows = c.fetchall()
    conn.close()
    return set(r[0] for r in rows)

def save_logro_db(user, logro_id):
    try:
        conn = sqlite3.connect('tequix_aprende.db')
        c = conn.cursor()
        c.execute("INSERT INTO logros (user, logro_id) VALUES (?,?)", (user, logro_id))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

# ══════════════════════════════════════════════
#  CURSOS: AGRONOMIA + INGLES
# ══════════════════════════════════════════════
COURSE_DATA = {
    "agronomia": [
        {
            "name": "Manejo sostenible del suelo", "emoji": "🌱",
            "texto": (
                "El suelo es el recurso mas importante de la agricultura. Un suelo sano tiene "
                "buena estructura, vida microbiana activa y materia organica suficiente. Para "
                "mantenerlo fertil usamos abonos organicos como compost y lombricomposta, "
                "evitamos la quema de residuos y practicamos la rotacion de cultivos. La "
                "cobertura vegetal protege el suelo de la erosion y mejora su retencion de agua. "
                "Se recomienda analizar el suelo cada ciclo agricola para conocer sus necesidades "
                "y tomar decisiones acertadas de fertilizacion y manejo."
            ),
            "questions": [
                {"p": "Que practica mejora la fertilidad del suelo?", "o": ["Quema de residuos", "Uso de abonos organicos", "Labranza intensiva"], "r": "Uso de abonos organicos"},
                {"p": "Que ayuda a prevenir la erosion?", "o": ["Dejar el suelo desnudo", "Cultivos de cobertura", "Uso excesivo de quimicos"], "r": "Cultivos de cobertura"},
                {"p": "Que tecnica mantiene la salud del suelo?", "o": ["Monocultivo", "Rotacion de cultivos", "Sobrepastoreo"], "r": "Rotacion de cultivos"},
                {"p": "Que indicador refleja un suelo sano?", "o": ["Baja materia organica", "Alta compactacion", "Buena estructura y vida microbiana"], "r": "Buena estructura y vida microbiana"},
                {"p": "Que reduce la perdida de nutrientes?", "o": ["Labranza excesiva", "Cobertura vegetal", "Uso de maquinaria pesada"], "r": "Cobertura vegetal"},
                {"p": "Que practica aumenta la materia organica?", "o": ["Uso de compost", "Quema de rastrojo", "Exceso de fertilizante"], "r": "Uso de compost"},
                {"p": "Cada cuando se recomienda analizar el suelo?", "o": ["Nunca", "Cada ciclo o anio", "Cada 10 anios"], "r": "Cada ciclo o anio"},
                {"p": "Que practica degrada el suelo?", "o": ["Rotacion", "Monocultivo continuo", "Compostaje"], "r": "Monocultivo continuo"},
                {"p": "Que mejora la retencion de agua?", "o": ["Suelo sin materia organica", "Materia organica alta", "Compactacion"], "r": "Materia organica alta"},
                {"p": "Que ayuda a conservar nutrientes?", "o": ["Lluvia sin cobertura", "Cobertura vegetal", "Quema"], "r": "Cobertura vegetal"},
            ]
        },
        {
            "name": "Uso eficiente del agua", "emoji": "💧",
            "texto": (
                "El agua es un recurso limitado y su uso eficiente es fundamental en la agricultura. "
                "El sistema de riego por goteo aplica agua directamente a la raiz con una eficiencia "
                "del 90-95%, siendo el mas recomendado. Regar en la madrugada o temprano por la "
                "manana reduce las perdidas por evaporacion. El mulch o acolchado conserva la humedad "
                "del suelo. Los sensores de humedad permiten regar solo cuando es necesario. "
                "La captacion de agua de lluvia y la programacion del riego son estrategias clave "
                "para enfrentar la sequia y reducir costos de produccion."
            ),
            "questions": [
                {"p": "Cual es el sistema de riego mas eficiente?", "o": ["Inundacion", "Goteo", "Manguera abierta"], "r": "Goteo"},
                {"p": "Que reduce el desperdicio de agua?", "o": ["Riego en horas de calor", "Riego por goteo", "Exceso de agua"], "r": "Riego por goteo"},
                {"p": "Cuando es mejor regar?", "o": ["Mediodia", "Tarde/noche", "Madrugada o temprano"], "r": "Madrugada o temprano"},
                {"p": "Que herramienta mide la humedad del suelo?", "o": ["Termometro", "Sensor de humedad", "Balanza"], "r": "Sensor de humedad"},
                {"p": "Que practica conserva agua en el suelo?", "o": ["Suelo desnudo", "Mulch (acolchado)", "Exceso de riego"], "r": "Mulch (acolchado)"},
                {"p": "Que fuente alternativa de agua se puede usar?", "o": ["Agua salada", "Agua de lluvia", "Agua contaminada"], "r": "Agua de lluvia"},
                {"p": "Que causa mayor perdida de agua?", "o": ["Goteo", "Evaporacion", "Sensores"], "r": "Evaporacion"},
                {"p": "Que cultivo requiere mas agua generalmente?", "o": ["Cactus", "Arroz", "Nopal"], "r": "Arroz"},
                {"p": "Que mejora la eficiencia del riego?", "o": ["Riego sin control", "Programacion del riego", "Exceso de agua"], "r": "Programacion del riego"},
                {"p": "Que ayuda a enfrentar la sequia?", "o": ["Desperdicio", "Tecnificacion del riego", "Suelo desnudo"], "r": "Tecnificacion del riego"},
            ]
        },
        {
            "name": "Control de plagas", "emoji": "🐛",
            "texto": (
                "El Manejo Integrado de Plagas (MIP) combina metodos biologicos, culturales y "
                "quimicos para controlar organismos daninos de forma sostenible. El control biologico "
                "usa enemigos naturales como depredadores e insectos beneficos para reducir plagas. "
                "La diversificacion de cultivos y la rotacion previenen su aparicion. El monitoreo "
                "periodico del campo permite detectar problemas a tiempo. Los productos quimicos "
                "deben ser el ultimo recurso y se debe rotar su uso para evitar resistencias. "
                "La prevencion siempre es mas economica que el control cuando ya hay dano."
            ),
            "questions": [
                {"p": "Que es el control integrado de plagas?", "o": ["Solo quimicos", "Uso combinado de metodos", "No hacer nada"], "r": "Uso combinado de metodos"},
                {"p": "Que es una plaga?", "o": ["Planta util", "Organismo que dania cultivos", "Fertilizante"], "r": "Organismo que dania cultivos"},
                {"p": "Que metodo de control es biologico?", "o": ["Insecticida", "Depredadores naturales", "Quema"], "r": "Depredadores naturales"},
                {"p": "Que previene las plagas?", "o": ["Monocultivo", "Diversificacion de cultivos", "Suelo desnudo"], "r": "Diversificacion de cultivos"},
                {"p": "Que evita la resistencia a pesticidas?", "o": ["Mismo quimico siempre", "Rotacion de productos", "Exceso de pesticida"], "r": "Rotacion de productos"},
                {"p": "Que es el monitoreo de cultivos?", "o": ["Ignorar cultivos", "Revisar periodicamente", "Aplicar quimicos a diario"], "r": "Revisar periodicamente"},
                {"p": "Que indica una posible enfermedad en la planta?", "o": ["Planta verde", "Manchas o deformacion", "Crecimiento normal"], "r": "Manchas o deformacion"},
                {"p": "Que reduce plagas de forma natural?", "o": ["Eliminar fauna", "Enemigos naturales", "Quimicos siempre"], "r": "Enemigos naturales"},
                {"p": "Que significa la prevencion en plagas?", "o": ["Actuar tarde", "Evitar aparicion de plagas", "No hacer nada"], "r": "Evitar aparicion de plagas"},
                {"p": "Que practica de control es sostenible?", "o": ["Exceso quimico", "Control integrado", "Monocultivo"], "r": "Control integrado"},
            ]
        },
        {
            "name": "Seleccion de cultivos", "emoji": "🌾",
            "texto": (
                "Elegir el cultivo correcto es clave para el exito agricola. Hay que considerar "
                "el clima, el tipo de suelo, el mercado y la disponibilidad de agua. Las semillas "
                "certificadas garantizan calidad, germinacion alta y resistencia a enfermedades. "
                "Las variedades locales estan mejor adaptadas al entorno. Diversificar los cultivos "
                "reduce riesgos ante condiciones climaticas adversas o caidas de precios. "
                "La planificacion antes de sembrar, analizando todos estos factores, es lo que "
                "distingue a un agricultor exitoso de uno que improvisa y pierde su cosecha."
            ),
            "questions": [
                {"p": "Que se debe considerar al elegir un cultivo?", "o": ["Solo el precio", "El clima del lugar", "El azar"], "r": "El clima del lugar"},
                {"p": "Que mejora el rendimiento del cultivo?", "o": ["Semillas certificadas", "Semillas desconocidas", "Suelo pobre"], "r": "Semillas certificadas"},
                {"p": "Que reduce los riesgos en produccion?", "o": ["Un solo cultivo", "Diversificacion", "Ignorar el clima"], "r": "Diversificacion"},
                {"p": "Que es la resistencia en un cultivo?", "o": ["Crecer lento", "Soportar plagas o sequia", "No producir"], "r": "Soportar plagas o sequia"},
                {"p": "Que factores afectan la eleccion del cultivo?", "o": ["Solo el clima", "Solo el mercado", "Clima, mercado y suelo"], "r": "Clima, mercado y suelo"},
                {"p": "Que es una semilla certificada?", "o": ["Sin control de calidad", "Calidad garantizada", "Semilla vieja"], "r": "Calidad garantizada"},
                {"p": "Que mejora la adaptacion del cultivo?", "o": ["Variedades locales", "Semillas aleatorias", "Ignorar el clima"], "r": "Variedades locales"},
                {"p": "Que afecta la germinacion?", "o": ["Solo la semilla", "Solo el agua", "Calidad, suelo y agua"], "r": "Calidad, suelo y agua"},
                {"p": "Que significa diversificar cultivos?", "o": ["Un solo cultivo", "Varios cultivos distintos", "No sembrar"], "r": "Varios cultivos distintos"},
                {"p": "Que reduce las perdidas de produccion?", "o": ["Planificacion", "Improvisar", "Monocultivo"], "r": "Planificacion"},
            ]
        },
        {
            "name": "Agricultura de precision", "emoji": "🚜",
            "texto": (
                "La agricultura de precision utiliza tecnologia para optimizar el uso de recursos "
                "y maximizar el rendimiento. Los drones permiten monitorear grandes extensiones en "
                "poco tiempo, detectando estres hidrico, plagas o deficiencias nutricionales. "
                "Los sensores de humedad, temperatura y nutrientes del suelo entregan datos en "
                "tiempo real para tomar mejores decisiones. El GPS permite mapear campos y aplicar "
                "insumos solo donde se necesita. Aunque el costo y la capacitacion son barreras, "
                "la agricultura de precision mejora la produccion, reduce costos y es mas sostenible."
            ),
            "questions": [
                {"p": "Que es la agricultura de precision?", "o": ["Agricultura tradicional", "Uso de tecnologia para optimizar", "Sin datos"], "r": "Uso de tecnologia para optimizar"},
                {"p": "Que herramienta tecnologica se usa en campo?", "o": ["Drones", "Palos", "Fuego"], "r": "Drones"},
                {"p": "Que miden los sensores agricolas?", "o": ["Solo humedad", "Solo temperatura", "Humedad, temperatura y suelo"], "r": "Humedad, temperatura y suelo"},
                {"p": "Que mejora el uso de tecnologia en el campo?", "o": ["Solo la produccion", "Solo los costos", "Produccion, costos y decisiones"], "r": "Produccion, costos y decisiones"},
                {"p": "Que herramienta registra datos del cultivo?", "o": ["Cuaderno o app", "Nada", "Solo memoria"], "r": "Cuaderno o app"},
                {"p": "Que ayuda a tomar mejores decisiones agricolas?", "o": ["Datos confiables", "Suerte", "Ignorar el cultivo"], "r": "Datos confiables"},
                {"p": "Que limita el acceso a la tecnologia agricola?", "o": ["Solo el costo", "Solo la capacitacion", "Costo, acceso y capacitacion"], "r": "Costo, acceso y capacitacion"},
                {"p": "Que ventaja tiene la agricultura de precision?", "o": ["Solo precision", "Solo ahorro", "Precision, ahorro y mejor manejo"], "r": "Precision, ahorro y mejor manejo"},
                {"p": "Para que se usa el GPS en agricultura?", "o": ["Ubicacion y mapeo de campos", "Regar", "Aplicar fertilizante"], "r": "Ubicacion y mapeo de campos"},
                {"p": "Que mejora directamente el rendimiento?", "o": ["Usar tecnologia y datos", "Ignorar datos", "Solo el azar"], "r": "Usar tecnologia y datos"},
            ]
        },
    ],
    "ingles": [
        {
            "name": "Greetings & Introductions", "emoji": "👋",
            "texto": (
                "In English, greetings change depending on the time and the level of formality. "
                "'Good morning' is used until noon, 'Good afternoon' from noon to 6 PM, and "
                "'Good evening' after 6 PM. 'Hello' and 'Hi' work at any time. "
                "To introduce yourself say 'My name is...' (formal) or 'I am...' (informal). "
                "When meeting someone for the first time say 'Nice to meet you'. "
                "To say goodbye use 'Goodbye' (formal) or 'Bye' / 'See you' (informal). "
                "Common responses to 'How are you?' are 'Fine, thank you' or 'Pretty good'."
            ),
            "questions": [
                {"p": "How do you say 'Hola'?", "o": ["Bye", "Hello", "Thanks"], "r": "Hello"},
                {"p": "How do you introduce yourself formally?", "o": ["Goodbye", "My name is...", "See you"], "r": "My name is..."},
                {"p": "What does 'Nice to meet you' mean?", "o": ["Goodbye", "Mucho gusto", "Sorry"], "r": "Mucho gusto"},
                {"p": "How do you say goodbye informally?", "o": ["Hello", "Bye", "Welcome"], "r": "Bye"},
                {"p": "What do you say when meeting someone for the first time?", "o": ["Good night", "Nice to meet you", "Sorry"], "r": "Nice to meet you"},
                {"p": "How do you say 'Buenos dias'?", "o": ["Good night", "Good morning", "Goodbye"], "r": "Good morning"},
                {"p": "What does 'See you' mean?", "o": ["Hello", "Nos vemos", "Sorry"], "r": "Nos vemos"},
                {"p": "How do you ask someone's name?", "o": ["How are you?", "What is your name?", "Where are you?"], "r": "What is your name?"},
                {"p": "What does 'Good afternoon' mean?", "o": ["Buenas noches", "Buenas tardes", "Buenos dias"], "r": "Buenas tardes"},
                {"p": "How do you respond to 'Hello'?", "o": ["Bye", "Hello", "Sorry"], "r": "Hello"},
            ]
        },
        {
            "name": "Simple Present Tense", "emoji": "⏰",
            "texto": (
                "The Simple Present is used for habits, routines and general truths. "
                "With I, You, We, They: use the base verb (go, eat, study). "
                "With He, She, It: add -s or -es to the verb (goes, eats, studies). "
                "Negative: use do not (don't) or does not (doesn't) + base verb. "
                "Questions: use Do or Does + subject + base verb. "
                "Examples: I study English. She works every day. They do not play soccer. "
                "Does he have a car? Time expressions: always, usually, sometimes, never, every day."
            ),
            "questions": [
                {"p": "Complete: 'I ___ a student.'", "o": ["is", "are", "am"], "r": "am"},
                {"p": "Complete: 'She ___ in a school.'", "o": ["work", "works", "working"], "r": "works"},
                {"p": "Complete: 'They ___ soccer.'", "o": ["plays", "play", "playing"], "r": "play"},
                {"p": "Which is correct?", "o": ["He go", "He goes", "He going"], "r": "He goes"},
                {"p": "Complete: 'We ___ happy.'", "o": ["is", "are", "am"], "r": "are"},
                {"p": "Complete: 'I ___ to school.'", "o": ["go", "goes", "going"], "r": "go"},
                {"p": "Complete: 'She ___ coffee.'", "o": ["drink", "drinks", "drinking"], "r": "drinks"},
                {"p": "Which is correct?", "o": ["They is", "They are", "They am"], "r": "They are"},
                {"p": "Complete: 'He ___ a car.'", "o": ["have", "has", "having"], "r": "has"},
                {"p": "Complete: 'We ___ English.'", "o": ["study", "studies", "studying"], "r": "study"},
            ]
        },
        {
            "name": "Everyday Vocabulary", "emoji": "📚",
            "texto": (
                "Knowing basic vocabulary in English is essential for communication. "
                "Family: mother (mama), father (papa), brother (hermano), sister (hermana). "
                "Colors: red (rojo), blue (azul), green (verde), yellow (amarillo), black (negro). "
                "Food: bread (pan), water (agua), apple (manzana), milk (leche), meat (carne). "
                "Numbers: one (1), two (2), three (3), ten (10), twenty (20), one hundred (100). "
                "Animals: dog (perro), cat (gato), bird (pajaro), fish (pez). "
                "Learning these words helps you understand and speak English in everyday situations."
            ),
            "questions": [
                {"p": "'Mother' means:", "o": ["Padre", "Madre", "Hermano"], "r": "Madre"},
                {"p": "'Apple' is a:", "o": ["Vegetable", "Fruit", "Meat"], "r": "Fruit"},
                {"p": "'Blue' means:", "o": ["Rojo", "Azul", "Verde"], "r": "Azul"},
                {"p": "'Ten' is the number:", "o": ["5", "10", "15"], "r": "10"},
                {"p": "'Bread' means:", "o": ["Leche", "Pan", "Agua"], "r": "Pan"},
                {"p": "'Father' means:", "o": ["Madre", "Padre", "Hijo"], "r": "Padre"},
                {"p": "'Dog' means:", "o": ["Gato", "Perro", "Pajaro"], "r": "Perro"},
                {"p": "'Green' means:", "o": ["Azul", "Verde", "Negro"], "r": "Verde"},
                {"p": "'Water' means:", "o": ["Fuego", "Agua", "Aire"], "r": "Agua"},
                {"p": "'One' is the number:", "o": ["1", "2", "3"], "r": "1"},
            ]
        },
        {
            "name": "Basic Questions", "emoji": "❓",
            "texto": (
                "Question words in English are called WH-words because most start with WH. "
                "What = Que (What is your name?), Where = Donde (Where do you live?), "
                "When = Cuando (When is your birthday?), Why = Por que (Why do you study?), "
                "Who = Quien (Who is your teacher?), How = Como (How are you?). "
                "To form a question use: WH-word + do/does + subject + base verb. "
                "Example: Where do you work? / What does she eat? / Why do they study? "
                "With the verb To Be: WH-word + am/is/are + subject? Example: How are you?"
            ),
            "questions": [
                {"p": "'Where' means:", "o": ["Que", "Donde", "Cuando"], "r": "Donde"},
                {"p": "'What' means:", "o": ["Que", "Donde", "Como"], "r": "Que"},
                {"p": "'How' means:", "o": ["Cuando", "Como", "Donde"], "r": "Como"},
                {"p": "'When' means:", "o": ["Como", "Cuando", "Donde"], "r": "Cuando"},
                {"p": "'Why' means:", "o": ["Por que", "Como", "Donde"], "r": "Por que"},
                {"p": "'Who' means:", "o": ["Que", "Quien", "Donde"], "r": "Quien"},
                {"p": "Which is correct?", "o": ["Where you live?", "Where do you live?", "Where you do live?"], "r": "Where do you live?"},
                {"p": "Which is correct?", "o": ["What is your name?", "What your name is?", "What name your is?"], "r": "What is your name?"},
                {"p": "Which is correct?", "o": ["How are you?", "How you are?", "You how are?"], "r": "How are you?"},
                {"p": "Which is correct?", "o": ["Why you study?", "Why do you study?", "Why you do study?"], "r": "Why do you study?"},
            ]
        },
        {
            "name": "Sentence Structure", "emoji": "📝",
            "texto": (
                "In English, sentences follow a fixed order: Subject + Verb + Complement. "
                "The subject is who does the action (She, He, They, I). "
                "The verb tells the action (eats, runs, studies, is). "
                "The complement gives more information (apples, fast, English). "
                "Example: She (subject) eats (verb) apples (complement). "
                "If you change the order the sentence becomes incorrect: 'Eats she apples' is wrong. "
                "This fixed order is one of the most important rules of English grammar. "
                "Practice: I play soccer. He is happy. They study English every day."
            ),
            "questions": [
                {"p": "Correct order in English:", "o": ["Verb + subject", "Subject + verb + complement", "Complement + verb"], "r": "Subject + verb + complement"},
                {"p": "'She eats apples' is:", "o": ["Incorrect", "Correct", "Incomplete"], "r": "Correct"},
                {"p": "'Eats she apples' is:", "o": ["Correct", "Incorrect", "Formal"], "r": "Incorrect"},
                {"p": "'I play soccer' has how many words:", "o": ["2 words", "3 words", "4 words"], "r": "3 words"},
                {"p": "'They study English' follows:", "o": ["Wrong order", "Correct order", "No verb"], "r": "Correct order"},
                {"p": "'He is happy' has structure:", "o": ["Subject + verb + complement", "Only verb", "Only subject"], "r": "Subject + verb + complement"},
                {"p": "Which is correct?", "o": ["She happy is", "She is happy", "Is she happy (statement)"], "r": "She is happy"},
                {"p": "What is the subject in 'She runs fast'?", "o": ["runs", "She", "fast"], "r": "She"},
                {"p": "What is the verb in 'The dog runs'?", "o": ["dog", "runs", "The"], "r": "runs"},
                {"p": "What is the complement in 'She eats apples'?", "o": ["eats", "She", "apples"], "r": "apples"},
            ]
        },
    ]
}

TOTAL_LESSONS = 5

LOGROS_DEF = [
    {"id": "primer_quiz",     "nombre": "Primer Paso",         "emoji": "🌱", "desc": "Completa tu primer quiz"},
    {"id": "agro_mod1",       "nombre": "Agricultor Novato",   "emoji": "🌿", "desc": "Completa el primer modulo de Agronomia"},
    {"id": "agro_completo",   "nombre": "Agricultor Maestro",  "emoji": "🚜", "desc": "Completa todos los modulos de Agronomia"},
    {"id": "ing_mod1",        "nombre": "Estudiante de Ingles","emoji": "💬", "desc": "Completa el primer modulo de Ingles"},
    {"id": "ing_completo",    "nombre": "Bilingue",            "emoji": "🌎", "desc": "Completa todos los modulos de Ingles"},
    {"id": "perfecto",        "nombre": "Perfeccionista",      "emoji": "⭐", "desc": "Obtén 100/100 en cualquier quiz"},
    {"id": "ambos_completos", "nombre": "Todólogo",            "emoji": "🎓", "desc": "Completa ambos cursos al 100%"},
    {"id": "racha3",          "nombre": "Racha x3",            "emoji": "🔥", "desc": "Aprueba 3 quizzes seguidos"},
    {"id": "sin_errores",     "nombre": "Sin Errores",         "emoji": "💎", "desc": "Completa un quiz sin ningun error"},
    {"id": "velocista",       "nombre": "Velocista",           "emoji": "⚡", "desc": "Termina un quiz en menos de 60 segundos"},
    {"id": "explorador",      "nombre": "Explorador",          "emoji": "🗺️", "desc": "Abre los dos cursos al menos una vez"},
    {"id": "lector",          "nombre": "Lector",              "emoji": "📖", "desc": "Lee el texto de 3 modulos distintos"},
]

# ══════════════════════════════════════════════
#  KV
# ══════════════════════════════════════════════
KV = '''
#:import SlideTransition kivy.uix.screenmanager.SlideTransition

<LessonItem>:
    padding: "14dp"
    size_hint_y: None
    height: "88dp"
    radius: [18,]
    elevation: 2
    md_bg_color: (0.91, 0.91, 0.91, 1) if self.is_locked else (1, 1, 1, 1)
    MDRelativeLayout:
        MDLabel:
            text: root.emoji_text + "  " + root.item_text
            pos_hint: {"center_y": .5, "x": .04}
            size_hint_x: .76
            theme_text_color: "Hint" if root.is_locked else "Primary"
            font_style: "Subtitle1"
            bold: not root.is_locked
            text_size: self.width, None
        MDLabel:
            text: "🔒" if root.is_locked else root.status_icon
            pos_hint: {"center_y": .5, "right": .97}
            font_size: "22sp"
            size_hint_x: .16
            halign: "right"
        Button:
            background_color: 0, 0, 0, 0
            on_release: if not root.is_locked: app.abrir_lectura(root.lesson_index)

ScreenManager:
    transition: SlideTransition(direction="left")
    LoginScreen:
    RegisterScreen:
    HomeScreen:
    LessonMenuScreen:
    TextoScreen:
    QuizScreen:
    LogrosScreen:

# ── LOGIN ────────────────────────────────────
<LoginScreen>:
    name: 'login'
    MDFloatLayout:
        md_bg_color: 1, 1, 1, 1
        MDFloatLayout:
            size_hint: None, None
            size: "560dp", "560dp"
            pos_hint: {"center_x": .5, "center_y": 1.08}
            canvas:
                Color:
                    rgba: (0.08, 0.45, 0.22, 1)
                Ellipse:
                    size: self.size
                    pos: self.pos
        MDLabel:
            text: "TequixAprende"
            font_style: "H4"
            pos_hint: {"center_y": .82}
            halign: "center"
            theme_text_color: "Custom"
            text_color: 1, 1, 1, 1
            bold: True
        MDLabel:
            text: "Agronomia  •  Ingles"
            font_style: "Caption"
            pos_hint: {"center_y": .75}
            halign: "center"
            theme_text_color: "Custom"
            text_color: 0.78, 1, 0.82, 1
        MDCard:
            size_hint: .87, None
            height: "340dp"
            pos_hint: {"center_x": .5, "center_y": .4}
            padding: "24dp"
            spacing: "10dp"
            orientation: "vertical"
            radius: [28,]
            elevation: 5
            MDLabel:
                text: "Iniciar Sesion"
                font_style: "H6"
                halign: "center"
                bold: True
                theme_text_color: "Custom"
                text_color: 0.08, 0.45, 0.22, 1
                size_hint_y: None
                height: "32dp"
            MDTextField:
                id: user
                hint_text: "Usuario"
                icon_right: "account"
                mode: "rectangle"
            MDTextField:
                id: password
                hint_text: "Contrasena"
                icon_right: "lock"
                password: True
                mode: "rectangle"
            MDLabel:
                id: login_error
                text: " "
                font_style: "Caption"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0.85, 0.1, 0.1, 1
                size_hint_y: None
                height: "20dp"
            MDFillRoundFlatButton:
                text: "ENTRAR"
                size_hint_x: 1
                md_bg_color: 0.08, 0.45, 0.22, 1
                on_release: root.login_user()
            MDFlatButton:
                text: "No tienes cuenta? Registrate"
                pos_hint: {"center_x": .5}
                theme_text_color: "Custom"
                text_color: 0.08, 0.45, 0.22, 1
                on_release: root.ir_registro()

# ── REGISTRO ─────────────────────────────────
<RegisterScreen>:
    name: 'register'
    MDFloatLayout:
        md_bg_color: 0.96, 0.97, 0.96, 1
        MDIconButton:
            icon: "arrow-left"
            pos_hint: {"top": .98, "x": 0}
            on_release: root.manager.current = 'login'
        MDLabel:
            text: "Crear Cuenta"
            font_style: "H5"
            halign: "center"
            pos_hint: {"center_y": .82}
            bold: True
            theme_text_color: "Custom"
            text_color: 0.08, 0.45, 0.22, 1
        MDCard:
            size_hint: .87, None
            height: "290dp"
            pos_hint: {"center_x": .5, "center_y": .5}
            padding: "24dp"
            spacing: "10dp"
            orientation: "vertical"
            radius: [28,]
            elevation: 4
            MDTextField:
                id: new_user
                hint_text: "Usuario (min. 3 caracteres)"
                mode: "rectangle"
            MDTextField:
                id: new_password
                hint_text: "Contrasena (min. 4 caracteres)"
                password: True
                mode: "rectangle"
            MDLabel:
                id: reg_msg
                text: " "
                font_style: "Caption"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0.85, 0.1, 0.1, 1
                size_hint_y: None
                height: "20dp"
            MDFillRoundFlatButton:
                text: "CREAR CUENTA"
                size_hint_x: 1
                md_bg_color: 0.08, 0.45, 0.22, 1
                on_release: root.register_user()

# ── HOME ─────────────────────────────────────
<HomeScreen>:
    name: 'home'
    MDFloatLayout:
        md_bg_color: 0.96, 0.97, 0.96, 1
        # Header verde
        MDBoxLayout:
            orientation: "vertical"
            size_hint_y: None
            height: "148dp"
            pos_hint: {"top": 1}
            padding: "20dp", "16dp"
            md_bg_color: 0.08, 0.45, 0.22, 1
            radius: [0, 0, 32, 32]
            MDBoxLayout:
                orientation: "horizontal"
                MDLabel:
                    id: welcome_label
                    text: "Hola!"
                    font_style: "H5"
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 1
                    bold: True
                MDIconButton:
                    icon: "trophy"
                    theme_text_color: "Custom"
                    text_color: 1, 0.88, 0.3, 1
                    pos_hint: {"center_y": .5}
                    on_release: app.ir_logros()
            MDLabel:
                text: "Bienvenido de nuevo a tu plataforma de aprendizaje"
                font_style: "Caption"
                theme_text_color: "Custom"
                text_color: 0.78, 1, 0.82, 1
        # Stats rápidas
        MDBoxLayout:
            orientation: "horizontal"
            size_hint_y: None
            height: "80dp"
            pos_hint: {"center_x": .5, "top": .74}
            padding: "14dp", "8dp"
            spacing: "10dp"
            # Mis cursos
            MDCard:
                padding: "10dp"
                radius: [16,]
                elevation: 2
                orientation: "vertical"
                md_bg_color: 1, 1, 1, 1
                MDLabel:
                    text: "📚"
                    font_size: "20sp"
                    halign: "center"
                    size_hint_y: None
                    height: "26dp"
                MDLabel:
                    text: "Mis cursos"
                    font_style: "Caption"
                    halign: "center"
                    bold: True
                MDLabel:
                    text: "2 activos"
                    font_style: "Caption"
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: 0.5, 0.5, 0.5, 1
            # Progreso general
            MDCard:
                padding: "10dp"
                radius: [16,]
                elevation: 2
                orientation: "vertical"
                md_bg_color: 1, 1, 1, 1
                MDLabel:
                    text: "📊"
                    font_size: "20sp"
                    halign: "center"
                    size_hint_y: None
                    height: "26dp"
                MDLabel:
                    text: "Progreso"
                    font_style: "Caption"
                    halign: "center"
                    bold: True
                MDLabel:
                    id: progreso_general_label
                    text: "0%"
                    font_style: "Caption"
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: 0.08, 0.45, 0.22, 1
            # Logros
            MDCard:
                padding: "10dp"
                radius: [16,]
                elevation: 2
                orientation: "vertical"
                md_bg_color: 1, 1, 1, 1
                MDLabel:
                    text: "🏆"
                    font_size: "20sp"
                    halign: "center"
                    size_hint_y: None
                    height: "26dp"
                MDLabel:
                    text: "Logros"
                    font_style: "Caption"
                    halign: "center"
                    bold: True
                MDLabel:
                    id: logros_home_stat
                    text: "0/12"
                    font_style: "Caption"
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: 0.6, 0.4, 0.0, 1
                Button:
                    background_color: 0, 0, 0, 0
                    size_hint: 1, 1
                    pos_hint: {"x": 0, "y": 0}
                    on_release: app.ir_logros()
        # Cards de cursos
        MDLabel:
            text: "Mis cursos"
            font_style: "H6"
            bold: True
            pos_hint: {"x": .05, "top": .56}
            size_hint_y: None
            height: "28dp"
            theme_text_color: "Custom"
            text_color: 0.15, 0.15, 0.15, 1
        MDScrollView:
            size_hint_y: None
            height: "316dp"
            pos_hint: {"center_x": .5, "top": .52}
            MDBoxLayout:
                orientation: "vertical"
                adaptive_height: True
                padding: "14dp"
                spacing: "14dp"
                # ── Card Agronomia ──
                MDCard:
                    padding: "16dp"
                    radius: [20,]
                    elevation: 3
                    orientation: "vertical"
                    spacing: "8dp"
                    md_bg_color: 0.9, 0.98, 0.92, 1
                    size_hint_y: None
                    height: "138dp"
                    MDBoxLayout:
                        orientation: "horizontal"
                        size_hint_y: None
                        height: "28dp"
                        MDLabel:
                            text: "Agronomia"
                            font_style: "H6"
                            bold: True
                            theme_text_color: "Custom"
                            text_color: 0.08, 0.40, 0.18, 1
                        MDLabel:
                            text: "En progreso"
                            font_style: "Caption"
                            halign: "right"
                            theme_text_color: "Custom"
                            text_color: 0.08, 0.45, 0.22, 1
                    MDLabel:
                        text: "Aprende sobre cultivos, suelos y manejo de recursos."
                        font_style: "Caption"
                        theme_text_color: "Custom"
                        text_color: 0.35, 0.35, 0.35, 1
                        size_hint_y: None
                        height: "28dp"
                    MDProgressBar:
                        value: app.prog_agro
                        color: 0.08, 0.5, 0.22, 1
                    MDLabel:
                        text: f"{int(app.prog_agro)}%  —  {int(app.agro_passed)}/{app.total_lessons} modulos"
                        font_style: "Caption"
                        theme_text_color: "Custom"
                        text_color: 0.4, 0.4, 0.4, 1
                    Button:
                        background_color: 0, 0, 0, 0
                        size_hint: 1, 1
                        pos_hint: {"x": 0, "y": 0}
                        on_release: app.ir_lecciones("agronomia")
                # ── Card Ingles ──
                MDCard:
                    padding: "16dp"
                    radius: [20,]
                    elevation: 3
                    orientation: "vertical"
                    spacing: "8dp"
                    md_bg_color: 0.88, 0.94, 1.0, 1
                    size_hint_y: None
                    height: "138dp"
                    MDBoxLayout:
                        orientation: "horizontal"
                        size_hint_y: None
                        height: "28dp"
                        MDLabel:
                            text: "Ingles"
                            font_style: "H6"
                            bold: True
                            theme_text_color: "Custom"
                            text_color: 0.08, 0.22, 0.55, 1
                        MDLabel:
                            text: "En progreso"
                            font_style: "Caption"
                            halign: "right"
                            theme_text_color: "Custom"
                            text_color: 0.12, 0.28, 0.65, 1
                    MDLabel:
                        text: "Desarrolla comprension, vocabulario y escritura."
                        font_style: "Caption"
                        theme_text_color: "Custom"
                        text_color: 0.35, 0.35, 0.35, 1
                        size_hint_y: None
                        height: "28dp"
                    MDProgressBar:
                        value: app.prog_ingles
                        color: 0.12, 0.28, 0.68, 1
                    MDLabel:
                        text: f"{int(app.prog_ingles)}%  —  {int(app.ingles_passed)}/{app.total_lessons} modulos"
                        font_style: "Caption"
                        theme_text_color: "Custom"
                        text_color: 0.4, 0.4, 0.4, 1
                    Button:
                        background_color: 0, 0, 0, 0
                        size_hint: 1, 1
                        pos_hint: {"x": 0, "y": 0}
                        on_release: app.ir_lecciones("ingles")

# ── MENU LECCIONES ───────────────────────────
<LessonMenuScreen>:
    name: 'lessons'
    MDFloatLayout:
        md_bg_color: 0.96, 0.97, 0.96, 1
        MDBoxLayout:
            size_hint_y: None
            height: "90dp"
            pos_hint: {"top": 1}
            padding: "12dp", "10dp"
            orientation: "horizontal"
            md_bg_color: 0.08, 0.45, 0.22, 1
            radius: [0, 0, 28, 28]
            MDIconButton:
                icon: "chevron-left"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                on_release:
                    root.manager.transition.direction = "right"
                    root.manager.current = 'home'
            MDLabel:
                id: menu_title
                text: "Modulos"
                font_style: "H6"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                bold: True
                valign: "center"
        MDScrollView:
            size_hint_y: .82
            pos_hint: {"top": .82}
            MDBoxLayout:
                id: lesson_list
                orientation: "vertical"
                adaptive_height: True
                padding: "14dp"
                spacing: "12dp"

# ── PANTALLA TEXTO ───────────────────────────
<TextoScreen>:
    name: 'texto'
    MDFloatLayout:
        md_bg_color: 0.96, 0.97, 0.96, 1
        MDBoxLayout:
            size_hint_y: None
            height: "90dp"
            pos_hint: {"top": 1}
            padding: "12dp", "10dp"
            orientation: "horizontal"
            md_bg_color: 0.08, 0.45, 0.22, 1
            radius: [0, 0, 28, 28]
            MDIconButton:
                icon: "chevron-left"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                on_release:
                    root.manager.transition.direction = "right"
                    root.manager.current = 'lessons'
            MDLabel:
                id: texto_titulo
                text: "Lectura"
                font_style: "H6"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                bold: True
                valign: "center"
        MDScrollView:
            size_hint_y: .70
            pos_hint: {"center_x": .5, "top": .82}
            MDCard:
                padding: "18dp"
                radius: [18,]
                elevation: 2
                adaptive_height: True
                md_bg_color: 1, 1, 1, 1
                MDLabel:
                    id: texto_contenido
                    text: ""
                    font_style: "Body1"
                    theme_text_color: "Primary"
                    text_size: self.width - 36, None
                    size_hint_y: None
                    height: self.texture_size[1]
                    halign: "justify"
                    line_height: 1.5
        MDFillRoundFlatButton:
            text: "Iniciar Quiz"
            size_hint_x: .82
            pos_hint: {"center_x": .5, "y": .04}
            md_bg_color: 0.08, 0.45, 0.22, 1
            on_release: app.ir_quiz()

# ── QUIZ ─────────────────────────────────────
<QuizScreen>:
    name: 'quiz'
    MDFloatLayout:
        md_bg_color: 0.96, 0.97, 0.96, 1
        MDIconButton:
            icon: "close-circle-outline"
            pos_hint: {"top": .99, "right": .99}
            theme_text_color: "Custom"
            text_color: 0.55, 0.55, 0.55, 1
            on_release: root.confirmar_salida()
        MDCard:
            size_hint: .92, .88
            pos_hint: {"center_x": .5, "center_y": .48}
            radius: [22,]
            padding: "20dp"
            spacing: "10dp"
            orientation: "vertical"
            elevation: 4
            MDLabel:
                id: progress_label
                text: "Pregunta 1 de 10"
                font_style: "Caption"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0.55, 0.55, 0.55, 1
                size_hint_y: None
                height: "22dp"
            MDProgressBar:
                id: quiz_progress
                value: 0
                size_hint_y: None
                height: "6dp"
                color: 0.08, 0.45, 0.22, 1
            MDLabel:
                id: quiz_module_label
                text: ""
                font_style: "Caption"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0.35, 0.5, 0.35, 1
                size_hint_y: None
                height: "18dp"
            MDLabel:
                id: q_label
                text: ""
                halign: "center"
                font_style: "H6"
                size_hint_y: .38
                text_size: self.width, None
                valign: "middle"
                bold: True
            MDBoxLayout:
                orientation: "vertical"
                spacing: "12dp"
                MDRaisedButton:
                    id: b1
                    size_hint_x: 1
                    md_bg_color: 0.08, 0.45, 0.22, 1
                    on_release: root.responder(self.text)
                MDRaisedButton:
                    id: b2
                    size_hint_x: 1
                    md_bg_color: 0.08, 0.45, 0.22, 1
                    on_release: root.responder(self.text)
                MDRaisedButton:
                    id: b3
                    size_hint_x: 1
                    md_bg_color: 0.08, 0.45, 0.22, 1
                    on_release: root.responder(self.text)

# ── LOGROS ───────────────────────────────────
<LogrosScreen>:
    name: 'logros'
    MDFloatLayout:
        md_bg_color: 0.96, 0.97, 0.96, 1
        MDBoxLayout:
            size_hint_y: None
            height: "90dp"
            pos_hint: {"top": 1}
            padding: "12dp", "10dp"
            orientation: "horizontal"
            md_bg_color: 0.48, 0.32, 0.0, 1
            radius: [0, 0, 28, 28]
            MDIconButton:
                icon: "chevron-left"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                on_release:
                    root.manager.transition.direction = "right"
                    root.manager.current = 'home'
            MDLabel:
                text: "Mis Logros"
                font_style: "H6"
                theme_text_color: "Custom"
                text_color: 1, 0.9, 0.5, 1
                bold: True
                valign: "center"
        MDLabel:
            id: logros_count
            text: "0 / 12 desbloqueados"
            font_style: "Caption"
            halign: "center"
            pos_hint: {"center_x": .5, "top": .82}
            size_hint_y: None
            height: "24dp"
            theme_text_color: "Custom"
            text_color: 0.5, 0.35, 0.0, 1
        MDScrollView:
            size_hint_y: .76
            pos_hint: {"top": .79}
            MDBoxLayout:
                id: logros_list
                orientation: "vertical"
                adaptive_height: True
                padding: "14dp"
                spacing: "10dp"
'''

# ══════════════════════════════════════════════
#  WIDGETS
# ══════════════════════════════════════════════
class LessonItem(MDCard):
    item_text    = StringProperty("")
    emoji_text   = StringProperty("📖")
    status_icon  = StringProperty("▶️")
    is_locked    = BooleanProperty(True)
    lesson_index = NumericProperty(0)

def make_lesson_item(text, emoji, locked, done, index):
    item = LessonItem()
    item.item_text    = text
    item.emoji_text   = emoji
    item.is_locked    = locked
    item.status_icon  = "✅" if done else "▶️"
    item.lesson_index = index
    return item

# ══════════════════════════════════════════════
#  PANTALLAS
# ══════════════════════════════════════════════
class LoginScreen(Screen):
    def ir_registro(self):
        self.ids.login_error.text = " "
        self.manager.current = 'register'

    def login_user(self):
        self.ids.login_error.text = " "
        user = self.ids.user.text.strip()
        pwd  = self.ids.password.text
        if not user or not pwd:
            self.ids.login_error.text = "Completa todos los campos"
            return
        if not user_exists(user):
            self.ids.login_error.text = "Ese usuario no existe"
            return
        if not check_login(user, pwd):
            self.ids.login_error.text = "Contrasena incorrecta"
            return
        app = MDApp.get_running_app()
        app.current_user = user
        app.cargar_progreso()
        self.ids.user.text     = ""
        self.ids.password.text = ""
        self.ids.login_error.text = " "
        self.manager.current = 'home'


class RegisterScreen(Screen):
    def register_user(self):
        self.ids.reg_msg.text_color = (0.85, 0.1, 0.1, 1)
        user = self.ids.new_user.text.strip()
        pwd  = self.ids.new_password.text
        if len(user) < 3:
            self.ids.reg_msg.text = "Usuario: minimo 3 caracteres"
            return
        if len(pwd) < 4:
            self.ids.reg_msg.text = "Contrasena: minimo 4 caracteres"
            return
        if register_user_db(user, pwd):
            self.ids.reg_msg.text_color = (0.08, 0.45, 0.22, 1)
            self.ids.reg_msg.text = "Cuenta creada! Inicia sesion"
            self.ids.new_user.text     = ""
            self.ids.new_password.text = ""
            Clock.schedule_once(lambda dt: self._ir_login(), 1.3)
        else:
            self.ids.reg_msg.text = "Ese usuario ya existe"

    def _ir_login(self):
        self.ids.reg_msg.text = " "
        self.manager.current = 'login'


class HomeScreen(Screen):
    def on_enter(self):
        app = MDApp.get_running_app()
        self.ids.welcome_label.text = f"Hola, {app.current_user}! 👋"
        total_logros = len(app.logros_desbloqueados)
        self.ids.logros_home_stat.text = f"{total_logros}/{len(LOGROS_DEF)}"
        promedio = (app.prog_agro + app.prog_ingles) / 2
        self.ids.progreso_general_label.text = f"{int(promedio)}%"
        app.check_explorador()


class LessonMenuScreen(Screen):
    def on_enter(self):
        app    = MDApp.get_running_app()
        course = app.current_course
        passed = app.agro_passed if course == "agronomia" else app.ingles_passed
        data   = COURSE_DATA[course]
        self.ids.lesson_list.clear_widgets()
        self.ids.menu_title.text = "Agronomia" if course == "agronomia" else "Ingles"
        for i in range(TOTAL_LESSONS):
            locked = (i > passed)
            done   = (i < passed)
            item = make_lesson_item(
                text   = f"M{i+1}: {data[i]['name']}",
                emoji  = data[i]['emoji'],
                locked = locked,
                done   = done,
                index  = i,
            )
            self.ids.lesson_list.add_widget(item)


class TextoScreen(Screen):
    def on_enter(self):
        app    = MDApp.get_running_app()
        lesson = COURSE_DATA[app.current_course][app.current_lesson]
        self.ids.texto_titulo.text    = f"{lesson['emoji']}  {lesson['name']}"
        self.ids.texto_contenido.text = lesson['texto']
        # Logro lector
        app.textos_leidos.add(f"{app.current_course}_{app.current_lesson}")
        if len(app.textos_leidos) >= 3:
            app._desbloquear("lector")


class QuizScreen(Screen):
    def on_pre_enter(self):
        app    = MDApp.get_running_app()
        lesson = COURSE_DATA[app.current_course][app.current_lesson]
        self.questions  = lesson["questions"]
        self.idx        = 0
        self.correct    = 0
        self.errores    = 0
        self.start_time = time.time()
        self.ids.quiz_module_label.text = f"{lesson['emoji']}  {lesson['name']}"
        self._update_q()

    def _update_q(self):
        if self.idx < len(self.questions):
            q     = self.questions[self.idx]
            total = len(self.questions)
            self.ids.progress_label.text = f"Pregunta {self.idx+1} de {total}"
            self.ids.quiz_progress.value = (self.idx / total) * 100
            self.ids.q_label.text = q["p"]
            self.ids.b1.text = q["o"][0]
            self.ids.b2.text = q["o"][1]
            self.ids.b3.text = q["o"][2]
            for b in ["b1", "b2", "b3"]:
                self.ids[b].disabled    = False
                self.ids[b].md_bg_color = (0.08, 0.45, 0.22, 1)
        else:
            self._mostrar_resultado()

    def responder(self, texto):
        for b in ["b1", "b2", "b3"]:
            self.ids[b].disabled = True
        correcta = self.questions[self.idx]["r"]
        if texto == correcta:
            self.correct += 1
            for b in ["b1", "b2", "b3"]:
                if self.ids[b].text == texto:
                    self.ids[b].md_bg_color = (0.08, 0.70, 0.28, 1)
        else:
            self.errores += 1
            for b in ["b1", "b2", "b3"]:
                if self.ids[b].text == texto:
                    self.ids[b].md_bg_color = (0.85, 0.18, 0.18, 1)
                if self.ids[b].text == correcta:
                    self.ids[b].md_bg_color = (0.08, 0.70, 0.28, 1)
        self.idx += 1
        Clock.schedule_once(lambda dt: self._update_q(), 0.7)

    def confirmar_salida(self):
        self._exit_dialog = MDDialog(
            title="Salir del quiz",
            text="Seguro? No se guardara tu avance en este quiz.",
            buttons=[
                MDFlatButton(text="CANCELAR",
                             on_release=lambda x: self._exit_dialog.dismiss()),
                MDRaisedButton(text="SALIR",
                               md_bg_color=(0.8, 0.15, 0.15, 1),
                               on_release=lambda x: self._forzar_salida()),
            ]
        )
        self._exit_dialog.open()

    def _forzar_salida(self):
        self._exit_dialog.dismiss()
        self.manager.transition.direction = "right"
        self.manager.current = 'lessons'

    def _mostrar_resultado(self):
        elapsed = time.time() - self.start_time
        score   = (self.correct / len(self.questions)) * 100
        app     = MDApp.get_running_app()
        nuevos  = []

        if score >= 80:
            avanzado = False
            if app.current_course == "agronomia" and app.current_lesson == int(app.agro_passed):
                app.agro_passed += 1
                set_progress(app.current_user, "agronomia", int(app.agro_passed))
                avanzado = True
            elif app.current_course == "ingles" and app.current_lesson == int(app.ingles_passed):
                app.ingles_passed += 1
                set_progress(app.current_user, "ingles", int(app.ingles_passed))
                avanzado = True

            estrellas = "⭐⭐⭐" if score == 100 else "⭐⭐"
            msg = f"{estrellas}  {score:.0f} / 100\nModulo completado!"
            if avanzado:
                msg += "\n Siguiente modulo desbloqueado!"

            nuevos = app.check_logros(score, elapsed, self.errores)
        else:
            msg = f"Puntaje: {score:.0f} / 100\nNecesitas al menos 80 para avanzar."

        if nuevos:
            msg += "\n\nLogros desbloqueados!\n" + "\n".join(
                f"  {l['emoji']} {l['nombre']}" for l in nuevos
            )

        self._result_dialog = MDDialog(
            title="Resultado",
            text=msg,
            buttons=[MDRaisedButton(
                text="OK",
                md_bg_color=(0.08, 0.45, 0.22, 1),
                on_release=lambda x: self._cerrar_resultado()
            )]
        )
        self._result_dialog.open()

    def _cerrar_resultado(self):
        self._result_dialog.dismiss()
        self.manager.transition.direction = "right"
        self.manager.current = 'lessons'


class LogrosScreen(Screen):
    def on_enter(self):
        app      = MDApp.get_running_app()
        unlocked = app.logros_desbloqueados
        count    = sum(1 for l in LOGROS_DEF if l["id"] in unlocked)
        self.ids.logros_count.text = f"{count} / {len(LOGROS_DEF)} desbloqueados"
        self.ids.logros_list.clear_widgets()
        for logro in LOGROS_DEF:
            self._add_logro_widget(logro, logro["id"] in unlocked)

    def _add_logro_widget(self, logro, is_ok):
        from kivy.graphics import Color as KColor, RoundedRectangle as KRR
        from kivy.uix.label import Label
        bg = (1.0, 1.0, 1.0, 1) if is_ok else (0.93, 0.93, 0.93, 1)
        row = BoxLayout(orientation="horizontal", size_hint_y=None,
                        height="76dp", padding="12dp", spacing="10dp")
        with row.canvas.before:
            KColor(rgba=bg)
            row._bg = KRR(size=row.size, pos=row.pos, radius=[14])
        row.bind(size=lambda w, v: setattr(w._bg, 'size', v),
                 pos=lambda w, v: setattr(w._bg, 'pos', v))

        emoji_lbl = Label(text=logro["emoji"], font_size="24sp",
                          size_hint=(None, 1), width="40dp",
                          halign="center", valign="middle",
                          opacity=1.0 if is_ok else 0.3)
        emoji_lbl.bind(size=lambda w, v: setattr(w, 'text_size', v))

        info = BoxLayout(orientation="vertical", spacing="2dp")
        nombre = Label(text=logro["nombre"], font_size="14sp", bold=True,
                       halign="left", valign="middle",
                       color=(0.05, 0.38, 0.15, 1) if is_ok else (0.55, 0.55, 0.55, 1),
                       size_hint_y=None, height="22dp")
        nombre.bind(size=lambda w, v: setattr(w, 'text_size', v))
        desc = Label(text=logro["desc"], font_size="11sp",
                     halign="left", valign="top",
                     color=(0.4, 0.4, 0.4, 1) if is_ok else (0.65, 0.65, 0.65, 1))
        desc.bind(size=lambda w, v: setattr(w, 'text_size', v))
        info.add_widget(nombre)
        info.add_widget(desc)

        estado = Label(text="✅" if is_ok else "🔒", font_size="20sp",
                       size_hint=(None, 1), width="34dp",
                       halign="center", valign="middle")
        estado.bind(size=lambda w, v: setattr(w, 'text_size', v))

        row.add_widget(emoji_lbl)
        row.add_widget(info)
        row.add_widget(estado)
        self.ids.logros_list.add_widget(row)


# ══════════════════════════════════════════════
#  APP PRINCIPAL
# ══════════════════════════════════════════════
class TequixApp(MDApp):
    prog_agro     = NumericProperty(0)
    prog_ingles   = NumericProperty(0)
    agro_passed   = NumericProperty(0)
    ingles_passed = NumericProperty(0)
    current_course = StringProperty("")
    current_lesson = NumericProperty(0)
    current_user   = StringProperty("")
    total_lessons  = NumericProperty(TOTAL_LESSONS)

    racha_actual         = 0
    cursos_visitados     = set()
    textos_leidos        = set()
    logros_desbloqueados = set()

    def on_agro_passed(self, *a):
        self.prog_agro = (self.agro_passed / TOTAL_LESSONS) * 100

    def on_ingles_passed(self, *a):
        self.prog_ingles = (self.ingles_passed / TOTAL_LESSONS) * 100

    def cargar_progreso(self):
        self.agro_passed   = get_progress(self.current_user, "agronomia")
        self.ingles_passed = get_progress(self.current_user, "ingles")
        self.logros_desbloqueados = get_logros(self.current_user)
        self.racha_actual     = 0
        self.cursos_visitados = set()
        self.textos_leidos    = set()

    def build(self):
        init_db()
        self.theme_cls.primary_palette = "Green"
        self.theme_cls.theme_style     = "Light"
        return Builder.load_string(KV)

    def ir_lecciones(self, course):
        self.current_course = course
        self.cursos_visitados.add(course)
        self.root.transition.direction = "left"
        self.root.current = 'lessons'

    def ir_logros(self):
        self.root.transition.direction = "left"
        self.root.current = 'logros'

    def abrir_lectura(self, index):
        self.current_lesson = index
        self.root.transition.direction = "left"
        self.root.current = 'texto'

    def ir_quiz(self):
        self.root.transition.direction = "left"
        self.root.current = 'quiz'

    def _desbloquear(self, logro_id):
        if logro_id not in self.logros_desbloqueados:
            if save_logro_db(self.current_user, logro_id):
                self.logros_desbloqueados.add(logro_id)
                return True
        return False

    def check_explorador(self):
        if len(self.cursos_visitados) >= 2:
            self._desbloquear("explorador")

    def check_logros(self, score, elapsed, errores):
        nuevos = []
        def maybe(lid):
            if self._desbloquear(lid):
                info = next(l for l in LOGROS_DEF if l["id"] == lid)
                nuevos.append(info)

        maybe("primer_quiz")
        if score == 100:
            maybe("perfecto")
        if errores == 0:
            maybe("sin_errores")
        if elapsed < 60:
            maybe("velocista")

        self.racha_actual += 1
        if self.racha_actual >= 3:
            maybe("racha3")

        if self.current_course == "agronomia":
            if self.current_lesson == 0:
                maybe("agro_mod1")
            if self.agro_passed >= TOTAL_LESSONS:
                maybe("agro_completo")
        else:
            if self.current_lesson == 0:
                maybe("ing_mod1")
            if self.ingles_passed >= TOTAL_LESSONS:
                maybe("ing_completo")

        if self.agro_passed >= TOTAL_LESSONS and self.ingles_passed >= TOTAL_LESSONS:
            maybe("ambos_completos")

        return nuevos


if __name__ == '__main__':
    TequixApp().run()