import sqlite3
import os
import hashlib

os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.core.window import Window
from kivy.properties import NumericProperty, StringProperty, BooleanProperty
from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.snackbar import Snackbar

Window.size = (360, 640)

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
    conn.commit()
    conn.close()

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

COURSE_DATA = {
    "agronomia": [
        {
            "name": "Manejo sostenible del suelo", "emoji": "🌱",
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
            "questions": [
                {"p": "How do you say 'Hola'?", "o": ["Bye", "Hello", "Thanks"], "r": "Hello"},
                {"p": "How do you introduce yourself?", "o": ["Goodbye", "My name is...", "See you"], "r": "My name is..."},
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

KV = '''
#:import SlideTransition kivy.uix.screenmanager.SlideTransition

<LessonItem>:
    padding: "15dp"
    size_hint_y: None
    height: "90dp"
    radius: [20,]
    elevation: 2
    md_bg_color: (0.92, 0.92, 0.92, 1) if self.is_locked else (1, 1, 1, 1)
    MDRelativeLayout:
        MDLabel:
            text: root.emoji_text + "  " + root.text
            pos_hint: {"center_y": .5, "x": .04}
            size_hint_x: .78
            theme_text_color: "Hint" if root.is_locked else "Primary"
            font_style: "Subtitle1"
            bold: not root.is_locked
            text_size: self.width, None
        MDLabel:
            text: "🔒" if root.is_locked else root.status_icon
            pos_hint: {"center_y": .5, "right": .96}
            font_size: "22sp"
            size_hint_x: .15
            halign: "right"
        Button:
            background_color: 0, 0, 0, 0
            on_release: if not root.is_locked: app.open_quiz(root.lesson_index)

ScreenManager:
    transition: SlideTransition(direction="left")
    LoginScreen:
    RegisterScreen:
    HomeScreen:
    LessonMenuScreen:
    QuizScreen:

<LoginScreen>:
    name: 'login'
    MDFloatLayout:
        md_bg_color: 1, 1, 1, 1
        MDFloatLayout:
            size_hint: None, None
            size: "600dp", "600dp"
            pos_hint: {"center_x": .5, "center_y": 1.1}
            canvas:
                Color:
                    rgba: (0.1, 0.5, 0.3, 1)
                Ellipse:
                    size: self.size
                    pos: self.pos
        MDLabel:
            text: "TequixAprende"
            font_style: "H4"
            pos_hint: {"center_y": .8}
            halign: "center"
            theme_text_color: "Custom"
            text_color: 1, 1, 1, 1
            bold: True
        MDLabel:
            text: "Aprende. Crece. Transforma."
            font_style: "Caption"
            pos_hint: {"center_y": .73}
            halign: "center"
            theme_text_color: "Custom"
            text_color: 0.85, 1, 0.85, 1
        MDCard:
            size_hint: .85, None
            height: "300dp"
            pos_hint: {"center_x": .5, "center_y": .42}
            padding: "25dp"
            spacing: "12dp"
            orientation: "vertical"
            radius: [30,]
            elevation: 4
            MDLabel:
                text: "Iniciar Sesion"
                font_style: "H6"
                halign: "center"
                bold: True
                theme_text_color: "Custom"
                text_color: 0.1, 0.5, 0.3, 1
            MDTextField:
                id: user
                hint_text: "Usuario"
                icon_right: "account"
                mode: "rectangle"
            MDTextField:
                id: password
                hint_text: "Contrasena"
                icon_right: "key"
                password: True
                mode: "rectangle"
            MDFillRoundFlatButton:
                text: "ENTRAR"
                size_hint_x: 1
                md_bg_color: 0.1, 0.5, 0.3, 1
                on_release: root.login_user()
            MDFlatButton:
                text: "No tienes cuenta? Registrate"
                pos_hint: {"center_x": .5}
                theme_text_color: "Custom"
                text_color: 0.1, 0.5, 0.3, 1
                on_release: root.manager.current = 'register'

<RegisterScreen>:
    name: 'register'
    MDFloatLayout:
        md_bg_color: 0.97, 0.97, 0.97, 1
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
        MDCard:
            size_hint: .85, None
            height: "240dp"
            pos_hint: {"center_x": .5, "center_y": .52}
            padding: "25dp"
            spacing: "12dp"
            orientation: "vertical"
            radius: [30,]
            elevation: 4
            MDTextField:
                id: new_user
                hint_text: "Nombre de usuario (min. 3 caracteres)"
                mode: "rectangle"
            MDTextField:
                id: new_password
                hint_text: "Contrasena (min. 4 caracteres)"
                password: True
                mode: "rectangle"
            MDFillRoundFlatButton:
                text: "CREAR CUENTA"
                size_hint_x: 1
                md_bg_color: 0.1, 0.5, 0.3, 1
                on_release: root.register_user()

<HomeScreen>:
    name: 'home'
    MDFloatLayout:
        md_bg_color: 0.97, 0.97, 0.97, 1
        MDBoxLayout:
            orientation: "vertical"
            size_hint_y: None
            height: "130dp"
            pos_hint: {"top": 1}
            padding: "20dp", "15dp"
            md_bg_color: 0.1, 0.5, 0.3, 1
            radius: [0, 0, 35, 35]
            MDLabel:
                id: welcome_label
                text: "Hola!"
                font_style: "H5"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                bold: True
            MDLabel:
                text: "Continua con tus cursos de hoy"
                font_style: "Caption"
                theme_text_color: "Custom"
                text_color: 0.85, 1, 0.85, 1
        MDScrollView:
            size_hint_y: None
            height: "390dp"
            pos_hint: {"center_x": .5, "top": .76}
            MDBoxLayout:
                orientation: "vertical"
                adaptive_height: True
                padding: "16dp"
                spacing: "16dp"
                MDCard:
                    padding: "20dp"
                    radius: [25,]
                    elevation: 3
                    orientation: "vertical"
                    spacing: "6dp"
                    md_bg_color: 0.9, 0.98, 0.92, 1
                    size_hint_y: None
                    height: "150dp"
                    MDLabel:
                        text: "Agronomia"
                        font_style: "H6"
                        bold: True
                        theme_text_color: "Custom"
                        text_color: 0.1, 0.45, 0.2, 1
                    MDProgressBar:
                        value: app.prog_agro
                        color: 0.1, 0.5, 0.25, 1
                    MDLabel:
                        text: f"Progreso: {int(app.prog_agro)}%  ({int(app.agro_passed)}/{app.total_lessons} modulos)"
                        font_style: "Caption"
                        theme_text_color: "Custom"
                        text_color: 0.4, 0.4, 0.4, 1
                    Button:
                        background_color: 0, 0, 0, 0
                        size_hint: 1, 1
                        pos_hint: {"x": 0, "y": 0}
                        on_release: app.go_to_lessons("agronomia")
                MDCard:
                    padding: "20dp"
                    radius: [25,]
                    elevation: 3
                    orientation: "vertical"
                    spacing: "6dp"
                    md_bg_color: 0.9, 0.93, 1.0, 1
                    size_hint_y: None
                    height: "150dp"
                    MDLabel:
                        text: "Ingles"
                        font_style: "H6"
                        bold: True
                        theme_text_color: "Custom"
                        text_color: 0.1, 0.25, 0.6, 1
                    MDProgressBar:
                        value: app.prog_ingles
                        color: 0.15, 0.35, 0.75, 1
                    MDLabel:
                        text: f"Progreso: {int(app.prog_ingles)}%  ({int(app.ingles_passed)}/{app.total_lessons} modulos)"
                        font_style: "Caption"
                        theme_text_color: "Custom"
                        text_color: 0.4, 0.4, 0.4, 1
                    Button:
                        background_color: 0, 0, 0, 0
                        size_hint: 1, 1
                        pos_hint: {"x": 0, "y": 0}
                        on_release: app.go_to_lessons("ingles")

<LessonMenuScreen>:
    name: 'lessons'
    MDFloatLayout:
        md_bg_color: 0.97, 0.97, 0.97, 1
        MDBoxLayout:
            size_hint_y: None
            height: "90dp"
            pos_hint: {"top": 1}
            padding: "15dp", "10dp"
            orientation: "horizontal"
            md_bg_color: 0.1, 0.5, 0.3, 1
            radius: [0, 0, 30, 30]
            MDIconButton:
                icon: "chevron-left"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                on_release:
                    root.manager.transition.direction = "right"
                    root.manager.current = 'home'
            MDLabel:
                id: menu_title
                text: "Plan de Estudios"
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
                padding: "16dp"
                spacing: "12dp"

<QuizScreen>:
    name: 'quiz'
    MDFloatLayout:
        md_bg_color: 0.97, 0.97, 0.97, 1
        MDCard:
            size_hint: .92, .88
            pos_hint: {"center_x": .5, "center_y": .5}
            radius: [25,]
            padding: "20dp"
            spacing: "10dp"
            orientation: "vertical"
            elevation: 4
            MDBoxLayout:
                size_hint_y: None
                height: "28dp"
                MDLabel:
                    id: progress_label
                    text: "Pregunta 1 de 10"
                    font_style: "Caption"
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: 0.5, 0.5, 0.5, 1
            MDProgressBar:
                id: quiz_progress
                value: 0
                size_hint_y: None
                height: "6dp"
                color: 0.1, 0.5, 0.3, 1
            MDLabel:
                id: quiz_module_label
                text: ""
                font_style: "Caption"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0.4, 0.4, 0.4, 1
                size_hint_y: None
                height: "20dp"
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
                    md_bg_color: 0.1, 0.5, 0.3, 1
                    on_release: root.answer(self.text)
                MDRaisedButton:
                    id: b2
                    size_hint_x: 1
                    md_bg_color: 0.1, 0.5, 0.3, 1
                    on_release: root.answer(self.text)
                MDRaisedButton:
                    id: b3
                    size_hint_x: 1
                    md_bg_color: 0.1, 0.5, 0.3, 1
                    on_release: root.answer(self.text)
'''

class LessonItem(MDCard):
    text         = StringProperty("")
    emoji_text   = StringProperty("📖")
    status_icon  = StringProperty("▶️")
    is_locked    = BooleanProperty(True)
    lesson_index = NumericProperty(0)


class LoginScreen(Screen):
    def login_user(self):
        user = self.ids.user.text.strip()
        pwd  = self.ids.password.text
        if not user or not pwd:
            Snackbar(text="Completa todos los campos").open()
            return
        conn = sqlite3.connect('tequix_aprende.db')
        c = conn.cursor()
        c.execute("SELECT * FROM usuarios WHERE user=? AND password=?", (user, hash_pwd(pwd)))
        result = c.fetchone()
        conn.close()
        if result:
            app = MDApp.get_running_app()
            app.current_user = user
            app.load_user_progress()
            self.manager.current = 'home'
        else:
            Snackbar(text="Usuario o contrasena incorrectos").open()


class RegisterScreen(Screen):
    def register_user(self):
        user = self.ids.new_user.text.strip()
        pwd  = self.ids.new_password.text
        if len(user) < 3:
            Snackbar(text="Usuario: minimo 3 caracteres").open()
            return
        if len(pwd) < 4:
            Snackbar(text="Contrasena: minimo 4 caracteres").open()
            return
        try:
            conn = sqlite3.connect('tequix_aprende.db')
            c = conn.cursor()
            c.execute("INSERT INTO usuarios (user, password) VALUES (?,?)", (user, hash_pwd(pwd)))
            conn.commit()
            conn.close()
            Snackbar(text="Cuenta creada. Inicia sesion!").open()
            self.manager.current = 'login'
        except sqlite3.IntegrityError:
            Snackbar(text="Ese usuario ya existe").open()


class HomeScreen(Screen):
    def on_enter(self):
        app = MDApp.get_running_app()
        self.ids.welcome_label.text = f"Hola, {app.current_user}!"


class LessonMenuScreen(Screen):
    def on_enter(self):
        app = MDApp.get_running_app()
        self.ids.lesson_list.clear_widgets()
        course = app.current_course
        passed = app.agro_passed if course == "agronomia" else app.ingles_passed
        data   = COURSE_DATA[course]
        self.ids.menu_title.text = "Agronomia" if course == "agronomia" else "Ingles"
        for i in range(TOTAL_LESSONS):
            locked = (i > passed)
            done   = (i < passed)
            item = LessonItem(
                text         = f"M{i+1}: {data[i]['name']}",
                emoji_text   = data[i]['emoji'],
                is_locked    = locked,
                lesson_index = i,
                status_icon  = "✅" if done else "▶️",
            )
            self.ids.lesson_list.add_widget(item)


class QuizScreen(Screen):
    def on_pre_enter(self):
        app    = MDApp.get_running_app()
        lesson = COURSE_DATA[app.current_course][app.current_lesson]
        self.questions = lesson["questions"]
        self.idx     = 0
        self.correct = 0
        self.ids.quiz_module_label.text = lesson['name']
        self.update_q()

    def update_q(self):
        if self.idx < len(self.questions):
            q     = self.questions[self.idx]
            total = len(self.questions)
            self.ids.progress_label.text = f"Pregunta {self.idx+1} de {total}"
            self.ids.quiz_progress.value = (self.idx / total) * 100
            self.ids.q_label.text = q["p"]
            self.ids.b1.text = q["o"][0]
            self.ids.b2.text = q["o"][1]
            self.ids.b3.text = q["o"][2]
            for bid in ["b1", "b2", "b3"]:
                self.ids[bid].disabled = False
                self.ids[bid].md_bg_color = (0.1, 0.5, 0.3, 1)
        else:
            self.show_result()

    def answer(self, text):
        for bid in ["b1", "b2", "b3"]:
            self.ids[bid].disabled = True
        correct_answer = self.questions[self.idx]["r"]
        if text == correct_answer:
            self.correct += 1
            for bid in ["b1", "b2", "b3"]:
                if self.ids[bid].text == text:
                    self.ids[bid].md_bg_color = (0.1, 0.75, 0.3, 1)
        else:
            for bid in ["b1", "b2", "b3"]:
                if self.ids[bid].text == text:
                    self.ids[bid].md_bg_color = (0.85, 0.2, 0.2, 1)
                if self.ids[bid].text == correct_answer:
                    self.ids[bid].md_bg_color = (0.1, 0.75, 0.3, 1)
        self.idx += 1
        Clock.schedule_once(lambda dt: self.update_q(), 0.7)

    def show_result(self):
        score = (self.correct / len(self.questions)) * 100
        app   = MDApp.get_running_app()
        if score >= 80:
            if app.current_course == "agronomia" and app.current_lesson == app.agro_passed:
                app.agro_passed += 1
                set_progress(app.current_user, "agronomia", int(app.agro_passed))
            elif app.current_course == "ingles" and app.current_lesson == app.ingles_passed:
                app.ingles_passed += 1
                set_progress(app.current_user, "ingles", int(app.ingles_passed))
            stars = "⭐⭐⭐" if score == 100 else "⭐⭐"
            msg = f"{stars} Excelente! {score:.0f}/100\nModulo completado!"
        else:
            msg = f"Puntaje: {score:.0f}/100\nNecesitas al menos 80 para avanzar."
        self.dialog = MDDialog(
            title="Resultado del Quiz",
            text=msg,
            buttons=[MDRaisedButton(
                text="OK",
                md_bg_color=(0.1, 0.5, 0.3, 1),
                on_release=lambda x: self.close_dialog()
            )]
        )
        self.dialog.open()

    def close_dialog(self):
        self.dialog.dismiss()
        self.manager.current = 'lessons'


class TequixApp(MDApp):
    prog_agro     = NumericProperty(0)
    prog_ingles   = NumericProperty(0)
    agro_passed   = NumericProperty(0)
    ingles_passed = NumericProperty(0)
    current_course  = StringProperty("")
    current_lesson  = NumericProperty(0)
    current_user    = StringProperty("")
    total_lessons   = NumericProperty(TOTAL_LESSONS)

    def on_agro_passed(self, instance, value):
        self.prog_agro = (value / TOTAL_LESSONS) * 100

    def on_ingles_passed(self, instance, value):
        self.prog_ingles = (value / TOTAL_LESSONS) * 100

    def load_user_progress(self):
        """Carga el progreso guardado del usuario en la BD."""
        self.agro_passed   = get_progress(self.current_user, "agronomia")
        self.ingles_passed = get_progress(self.current_user, "ingles")

    def build(self):
        init_db()
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.theme_style = "Light"
        return Builder.load_string(KV)

    def go_to_lessons(self, course):
        self.current_course = course
        self.root.transition.direction = "left"
        self.root.current = 'lessons'

    def open_quiz(self, index):
        self.current_lesson = index
        self.root.current = 'quiz'


if __name__ == '__main__':
    TequixApp().run()