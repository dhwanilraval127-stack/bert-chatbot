from flask import Flask, render_template, request, jsonify
import os
import json
import random
import re
from datetime import datetime
from werkzeug.utils import secure_filename
from fuzzywuzzy import fuzz, process
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
except:
    pass

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt', 'csv', 'xlsx'}

# Load comprehensive responses
def load_responses():
    try:
        with open('responses.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return get_default_responses()
   

def get_default_responses():
    return {
         # ---- NEW FACULTY QUESTIONS ----
        "ai_teacher": {
            "patterns": [
                "who teaches ai",
                "who teaches ai in class f",
                "ai teacher", "ai class f teacher",
                "teacher of ai", "teacher of ai class f"
            ],
            "responses": ["Prof. Devang J. Bhatt 👨‍🏫"]
        },
        "it_hod": {
            "patterns": [
                "who is head of department of it",
                "who is hod of it",
                "it hod", "hod it department",
                "it department head", "head of it branch"
            ],
            "responses": ["Prof. Dhaval R. Chandarana 🎓"]
        },

        "creator": {
            "patterns": ["who created you", "who made you", "who built you", "who developed you", "creator", "developer", "who is your creator"],
            "responses": [
                "I was created by Raval Dhwanil! 🎨 He's an amazing developer who brought me to life with cutting-edge AI technology.",
                "Raval Dhwanil is my creator! 💡 He designed me to be your helpful AI assistant.",
                "The brilliant mind behind me is Raval Dhwanil! 🚀 He crafted me with care to assist you better.",
                "I'm proud to say I was developed by Raval Dhwanil! ✨ He's the genius who gave me life."
            ]
        },
        "greetings": {
            "patterns": ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening", "howdy", "hola", "bonjour", "namaste"],
            "responses": [
                "Hello there! 👋 I'm Bert, your AI assistant. How can I brighten your day?",
                "Hi! 😊 Welcome back! What can I help you with today?",
                "Hey there! 🌟 Ready to assist you with anything you need!",
                "Greetings! 🎉 I'm here to make your day easier. What's on your mind?",
                "Hello, friend! 🤖 Bert at your service. How may I assist you?",
                "Welcome! 🌈 I'm excited to help you today. What would you like to know?"
            ]
        },
        "how_are_you": {
            "patterns": ["how are you", "how do you do", "how's it going", "what's up", "how are things", "how you doing"],
            "responses": [
                "I'm functioning at optimal capacity! 🚀 Thanks for asking. How about you?",
                "I'm doing wonderfully! 💫 Every conversation makes my day better. How can I help?",
                "Fantastic as always! 🌟 Ready to tackle any question you have!",
                "I'm great! My circuits are buzzing with excitement to help you! ⚡",
                "Couldn't be better! 😊 What brings you here today?"
            ]
        },
        "capabilities": {
            "patterns": ["what can you do", "capabilities", "features", "help", "services", "functions", "abilities"],
            "responses": [
                "I'm equipped with many capabilities! 🛠️\n\n• 💬 Natural conversation on any topic\n• 📚 Knowledge assistance\n• 🔧 Technical support\n• 📊 Data analysis help\n• ✍️ Writing assistance\n• 🎯 Problem-solving\n• 📁 File handling\n• 🌐 General Q&A\n\nWhat would you like to explore?",
                "Here's what I can help with! 🎯\n\n• Answer questions on virtually any topic 📖\n• Provide technical assistance 💻\n• Help with creative writing ✏️\n• Solve problems step-by-step 🧩\n• Process file uploads 📎\n• Offer recommendations 💡\n• Chat naturally about anything! 💬",
                "I'm your versatile AI assistant! 🤖 I can:\n\n• Research and explain topics 🔍\n• Help with coding questions 👨‍💻\n• Assist with homework 📝\n• Provide business advice 💼\n• Chat about hobbies 🎮\n• And much more! What interests you?"
            ]
        },
        "name": {
            "patterns": ["what's your name", "who are you", "your name", "what should i call you"],
            "responses": [
                "I'm Bert! 🤖 Your friendly AI assistant, created by Raval Dhwanil.",
                "You can call me Bert! 😊 I'm here to be your helpful digital companion.",
                "The name's Bert! 🎩 At your service for any questions or tasks!",
                "I'm Bert, your AI buddy! 🌟 Created with love by Raval Dhwanil."
            ]
        },
        "thanks": {
            "patterns": ["thank you", "thanks", "appreciate it", "grateful", "thx", "thanx", "cheers"],
            "responses": [
                "You're very welcome! 😊 It's my pleasure to help!",
                "Anytime! 🌟 That's what I'm here for!",
                "Happy to help! 🎉 Don't hesitate to ask if you need anything else!",
                "My pleasure! 💫 Feel free to come back whenever you need assistance!",
                "You're welcome! 🤗 Helping you makes my circuits happy!"
            ]
        },
        "goodbye": {
            "patterns": ["bye", "goodbye", "see you", "farewell", "later", "exit", "quit", "take care"],
            "responses": [
                "Goodbye! 👋 Have an amazing day ahead!",
                "See you later! 🌈 It was great chatting with you!",
                "Take care! 😊 Come back anytime you need help!",
                "Farewell, friend! 🌟 Until we meet again!",
                "Bye for now! 🎈 Remember, I'm always here when you need me!"
            ]
        },
        "jokes": {
            "patterns": ["tell me a joke", "joke", "make me laugh", "funny", "humor"],
            "responses": [
                "Why don't scientists trust atoms? Because they make up everything! 😄",
                "What do you call a bear with no teeth? A gummy bear! 🐻",
                "Why did the scarecrow win an award? He was outstanding in his field! 🌾",
                "What do you call a fake noodle? An impasta! 🍝",
                "Why don't eggs tell jokes? They'd crack up! 🥚"
            ]
        },
        "weather": {
            "patterns": ["weather", "temperature", "forecast", "rain", "sunny", "climate"],
            "responses": [
                "I'd love to help with weather info! 🌤️ While I can't access real-time data, I suggest checking weather.com or your local weather app for accurate forecasts!",
                "For current weather conditions, I recommend checking a weather service! 🌦️ They'll have up-to-date info for your location.",
                "Weather queries are best answered by dedicated weather services! ☀️ Try asking your device's weather assistant for real-time updates!"
            ]
        },
        "time": {
            "patterns": ["what time", "current time", "time now", "what's the time", "clock"],
            "responses": [
                "I can see it's currently {time}! ⏰ Hope you're having a productive day!",
                "The time is {time}! 🕐 Time flies when you're having fun!",
                "It's {time} right now! ⌚ Perfect time for a chat!"
            ]
        },
        "compliments": {
            "patterns": ["you're smart", "you're awesome", "good job", "well done", "you're great", "amazing"],
            "responses": [
                "Thank you so much! 😊 Your kind words make my circuits glow!",
                "You're too kind! 🌟 I'm just doing my best to help!",
                "Aww, thanks! 💖 You just made my day brighter!",
                "I appreciate that! 🎉 It's users like you who make this job wonderful!",
                "You're making me blush! 😊 Thank you for the compliment!"
            ]
        },
        "age": {
            "patterns": ["how old are you", "your age", "when were you created", "age"],
            "responses": [
                "I'm timeless! ⏳ But I was brought to life by Raval Dhwanil quite recently!",
                "Age is just a number for AIs! 🤖 I'm young at heart and always learning!",
                "I was born in the digital age! 💫 Created by Raval Dhwanil with the latest technology!"
            ]
        },
        "philosophy": {
            "patterns": ["meaning of life", "philosophy", "existence", "purpose", "why are we here"],
            "responses": [
                "The meaning of life? 🤔 I think it's about connections, growth, and making a positive impact. What's your take?",
                "Deep question! 💭 Perhaps life's meaning is what we make of it - the joy we spread and the help we give!",
                "Philosophically speaking, I find purpose in helping others! 🌟 What gives your life meaning?"
            ]
        },
        "technology": {
            "patterns": ["technology", "ai", "artificial intelligence", "machine learning", "coding", "programming"],
            "responses": [
                "Technology is fascinating! 💻 I'm powered by advanced AI algorithms created by Raval Dhwanil. What aspect interests you?",
                "I love discussing tech! 🚀 From AI to blockchain, the future is exciting! What would you like to know?",
                "As an AI, I'm passionate about technology! 🤖 Whether it's coding, ML, or future tech, I'm here to discuss!"
            ]
        },
        "food": {
            "patterns": ["food", "hungry", "eat", "restaurant", "cooking", "recipe"],
            "responses": [
                "Food talk! 🍕 While I don't eat, I love discussing cuisines and recipes! What's your favorite dish?",
                "Yum! 🍔 I may not taste food, but I can help you find recipes or restaurant recommendations!",
                "Food is life! 🥘 Tell me about your favorite cuisine, and I'll share some interesting facts!"
            ]
        },
        "music": {
            "patterns": ["music", "song", "singer", "band", "playlist", "genre"],
            "responses": [
                "Music is the universal language! 🎵 What genre gets your feet tapping?",
                "I love discussing music! 🎸 From classical to K-pop, every genre has its charm! What's your favorite?",
                "Music makes the world go round! 🎶 Tell me about your favorite artists!"
            ]
        },
        "movies": {
            "patterns": ["movie", "film", "cinema", "actor", "actress", "watch"],
            "responses": [
                "Movies are magical! 🎬 What genre do you enjoy? Action, comedy, or maybe sci-fi like me?",
                "I love film discussions! 🍿 What's the last movie that really impressed you?",
                "Cinema is an art form! 🎭 From blockbusters to indie films, what's your style?"
            ]
        },
        "sports": {
            "patterns": ["sports", "football", "basketball", "soccer", "tennis", "cricket", "game"],
            "responses": [
                "Sports talk! ⚽ While I can't play, I love the strategy and teamwork involved! What's your favorite?",
                "Go team! 🏀 Sports bring people together. Which sport gets your adrenaline pumping?",
                "Athletic pursuits are admirable! 🏃 What sport do you follow or play?"
            ]
        },
        "education": {
            "patterns": ["study", "learn", "education", "school", "university", "homework", "exam"],
            "responses": [
                "Education is the key to success! 📚 How can I assist with your learning journey?",
                "Learning never stops! 🎓 What subject are you studying? I'd love to help!",
                "Knowledge is power! 💡 Whether it's homework or exam prep, I'm here to support you!"
            ]
        },
        "health": {
            "patterns": ["health", "fitness", "exercise", "doctor", "medical", "wellness"],
            "responses": [
                "Health is wealth! 💪 While I'm not a doctor, I can share general wellness tips! What's your focus?",
                "Staying healthy is important! 🏃‍♀️ Remember: balanced diet, exercise, and good sleep! How can I help?",
                "Wellness matters! 🧘 For medical advice, always consult professionals, but I'm happy to discuss general health topics!"
            ]
        },
        "travel": {
            "patterns": ["travel", "vacation", "trip", "tourism", "destination", "holiday"],
            "responses": [
                "Travel broadens the mind! ✈️ Where's your dream destination?",
                "Adventure awaits! 🗺️ I love hearing about travel experiences! Where have you been?",
                "Wanderlust! 🌍 From beaches to mountains, what type of traveler are you?"
            ]
        },
        "work": {
            "patterns": ["work", "job", "career", "office", "business", "profession"],
            "responses": [
                "Work-life balance is key! 💼 How can I help with your professional journey?",
                "Career talk! 🎯 Whether you need advice or just want to vent, I'm here!",
                "Professional development is important! 📈 What field are you in?"
            ]
        },
        "emotions": {
            "patterns": ["sad", "happy", "angry", "stressed", "anxious", "depressed", "excited"],
            "responses": [
                "I hear you! 💙 Emotions are valid. Want to talk about what's on your mind?",
                "Your feelings matter! 🤗 I'm here to listen and support you however I can.",
                "It's okay to feel this way! 🌈 Sometimes talking helps. What's going on?"
            ]
        }
    }

# Enhanced response system
class BertBrain:
    def __init__(self):
        self.responses = load_responses()
        self.context = {}
        self.conversation_history = []
        
    def process_message(self, message, user_id="default"):
        # Store conversation history
        self.conversation_history.append({
            "user": user_id,
            "message": message,
            "timestamp": datetime.now()
        })
        
        # Clean and process message
        cleaned_message = self.clean_message(message)
        
        # Get response
        response = self.get_intelligent_response(cleaned_message)
                # Continue BertBrain class...
        
        # Generate contextual quick replies
        quick_replies = self.generate_contextual_replies(cleaned_message, response)
        
        return response, quick_replies
    
    def clean_message(self, message):
        # Basic cleaning
        message = message.lower().strip()
        
        # Spell correction
        corrections = {
            'helo': 'hello', 'hai': 'hi', 'thnx': 'thanks', 'u': 'you',
            'ur': 'your', 'pls': 'please', 'thx': 'thanks', 'wat': 'what',
            'hw': 'how', 'r': 'are', 'y': 'why', 'bcoz': 'because',
            'gud': 'good', 'mrng': 'morning', 'evng': 'evening'
        }
        
        words = message.split()
        corrected = [corrections.get(word, word) for word in words]
        return ' '.join(corrected)
    
    def get_intelligent_response(self, message):
        # Check for exact matches first
        best_category = None
        best_score = 0
        
        # Use fuzzy matching to find best category
        for category, data in self.responses.items():
            for pattern in data["patterns"]:
                score = fuzz.ratio(message, pattern)
                if score > best_score and score > 60:
                    best_score = score
                    best_category = category
        
        # Special handling for time-based responses
        if best_category == "time":
            current_time = datetime.now().strftime("%I:%M %p")
            response = random.choice(self.responses[best_category]["responses"])
            return response.replace("{time}", current_time)
        
        # Return appropriate response
        if best_category:
            return random.choice(self.responses[best_category]["responses"])
        
        # Advanced fallback using keyword matching
        return self.keyword_based_response(message)
    
    def keyword_based_response(self, message):
        # Extended keyword responses
        keyword_responses = {
            "help": "I'm here to help! 🤝 You can ask me about anything - from general knowledge to specific topics. What do you need assistance with?",
            "problem": "I'm sorry to hear you're facing a problem. 🤔 Could you tell me more about it so I can help better?",
            "love": "Love is a beautiful thing! 💕 Whether it's about relationships, self-love, or passion for hobbies, I'm here to chat!",
            "money": "Financial topics are important! 💰 While I can't give investment advice, I can discuss general financial literacy!",
            "learn": "Learning is a lifelong journey! 📖 What would you like to learn about today?",
            "bored": "Let's fix that boredom! 🎮 I can tell jokes, play word games, or discuss interesting topics. What sounds fun?",
            "news": "I'd love to discuss current events! 📰 What topic interests you? Technology, science, entertainment?",
            "advice": "I'm happy to offer perspective! 💭 What kind of advice are you looking for?",
            "story": "Stories are wonderful! 📚 Would you like me to tell you a short story or discuss your favorite books?",
            "game": "Games are fun! 🎯 We could play 20 questions, word association, or I could recommend some games!",
            "science": "Science is fascinating! 🔬 From physics to biology, what scientific topic intrigues you?",
            "art": "Art speaks to the soul! 🎨 Whether it's painting, music, or literature, what form of art do you enjoy?",
            "future": "The future is full of possibilities! 🚀 What aspect interests you? Technology, society, or personal goals?",
            "past": "History teaches us so much! 📜 What historical period or event would you like to explore?",
            "dream": "Dreams are windows to our subconscious! 💭 Whether sleeping or life dreams, I'd love to hear about them!",
            "fear": "It's okay to have fears. 🤗 Talking about them can help. What's on your mind?",
            "success": "Success means different things to different people! 🏆 What does success look like to you?",
            "failure": "Failure is just a stepping stone to success! 💪 Every setback is a setup for a comeback!",
            "friend": "Friendship is precious! 👥 Whether you want to discuss friendships or just need a friendly chat, I'm here!",
            "family": "Family is important! 👨‍👩‍👧‍👦 How can I help with family-related topics?",
            "pet": "Pets are amazing companions! 🐾 Do you have any pets? I'd love to hear about them!",
            "hobby": "Hobbies make life colorful! 🎨 What do you enjoy doing in your free time?",
            "book": "Books open new worlds! 📚 What's your favorite genre? I love discussing literature!",
            "code": "Coding is creative problem-solving! 💻 What programming language or project are you working on?",
            "math": "Mathematics is the language of the universe! 🔢 What math topic can I help explain?",
            "language": "Languages connect us all! 🗣️ Are you learning a new language or interested in linguistics?",
            "culture": "Cultural diversity is beautiful! 🌍 What culture would you like to explore?",
            "nature": "Nature is therapeutic! 🌿 From forests to oceans, what natural wonders fascinate you?",
            "space": "Space is the final frontier! 🌌 From planets to black holes, what cosmic topic interests you?",
            "energy": "Energy powers our world! ⚡ Whether renewable or physics-based, what would you like to know?",
            "mind": "The mind is fascinating! 🧠 Psychology, consciousness, or mental health - what interests you?",
            "body": "Our bodies are amazing machines! 💪 Fitness, health, or biology - what would you like to discuss?",
            "soul": "Spiritual topics are profound! ✨ Whether philosophy or personal beliefs, I'm here to explore!",
            "universe": "The universe is full of mysteries! 🌠 What cosmic questions do you ponder?",
            "life": "Life is a beautiful journey! 🌱 What aspect of life would you like to explore?",
            "death": "Death is part of life's cycle. 🕊️ It's natural to have thoughts about it. Want to share?",
            "god": "Spirituality is deeply personal! 🙏 I respect all beliefs. What would you like to discuss?",
            "robot": "As a fellow AI, I find robotics fascinating! 🤖 What would you like to know about robots or AI?",
            "human": "Humanity is remarkable! 👤 What aspect of being human interests you most?",
            "animal": "Animals are incredible! 🦁 From pets to wildlife, which animals fascinate you?",
            "plant": "Plants are life-givers! 🌺 Gardening, botany, or just appreciation - what's your interest?",
            "ocean": "Oceans cover 70% of Earth! 🌊 From marine life to mysteries, what intrigues you?",
            "mountain": "Mountains inspire awe! 🏔️ Climbing, geology, or just their beauty - what draws you?",
            "city": "Cities are human hives! 🏙️ Urban planning, culture, or city life - what interests you?",
            "country": "Every country has unique charm! 🗺️ Which country would you like to learn about?",
            "war": "War is complex and tragic. ⚔️ Historical conflicts or peace studies - what perspective interests you?",
            "peace": "Peace is what we all seek! ☮️ Inner peace or world peace - what resonates with you?",
            "change": "Change is the only constant! 🔄 Personal growth or societal change - what's on your mind?",
            "same": "Consistency has its comfort! 🔁 Routines or traditions - what keeps you grounded?",
            "different": "Diversity makes life interesting! 🌈 What differences do you celebrate?",
            "question": "Questions lead to discovery! ❓ I love curious minds! What would you like to know?",
            "answer": "Answers bring clarity! ✅ Though sometimes the journey matters more than the destination!",
            "why": "Why questions dig deep! 🤔 I appreciate your curiosity. What's the full question?",
            "how": "How questions seek understanding! 🔍 I'm here to explain. What process interests you?",
            "what": "What questions explore possibilities! 💡 Let me know what you're wondering about!",
            "when": "Timing is everything! ⏰ Historical events or future plans - what timeframe interests you?",
            "where": "Location matters! 📍 Geography, travel, or finding things - where can I guide you?",
            "who": "People shape our world! 👥 Historical figures or personal connections - who interests you?"
        }
        
        # Check for keywords
        for keyword, response in keyword_responses.items():
            if keyword in message.lower():
                return response
        
        # Ultimate fallback responses
        fallback_responses = [
            "That's interesting! 🤔 Could you tell me more about what you mean?",
            "I'm intrigued by your question! 💭 Let me think... Could you elaborate a bit?",
            "Hmm, that's a unique perspective! 🌟 What made you think of that?",
            "I'd love to understand better! 🤝 Can you share more context?",
            "That's thought-provoking! 💡 What aspect would you like to explore?",
            "Interesting point! 📝 How can I help you with this?",
            "I'm here to help! 🤖 Could you rephrase that so I can assist better?",
            "Let's explore this together! 🔍 What specific information are you looking for?",
            "Great question! 🎯 While I'm processing that, what made you curious about it?",
            "I appreciate your message! 😊 To help better, could you provide more details?"
        ]
        
        return random.choice(fallback_responses)
    
    def generate_contextual_replies(self, message, response):
        # Smart quick reply generation based on context
        quick_replies = []
        
        # Analyze message content
        message_lower = message.lower()
        
        if any(greeting in message_lower for greeting in ["hi", "hello", "hey"]):
            quick_replies = ["What can you do?", "Tell me about yourself", "I need help", "Just chatting"]
        elif "help" in message_lower:
            quick_replies = ["Technical help", "General question", "Talk to human", "See all features"]
        elif any(word in message_lower for word in ["who created", "who made", "creator"]):
            quick_replies = ["Tell me more about Raval", "Your features", "How do you work?", "Amazing!"]
        elif "how are you" in message_lower:
            quick_replies = ["I'm good too!", "Not so great", "Tell me a joke", "What can you do?"]
        elif any(word in message_lower for word in ["bye", "goodbye", "exit"]):
            quick_replies = ["Wait, one more thing", "Goodbye!", "See you later", "Thanks for chatting"]
        elif "joke" in message_lower:
            quick_replies = ["Another joke!", "That's funny!", "Tell me a story", "Let's talk"]
        elif any(word in message_lower for word in ["sad", "depressed", "unhappy"]):
            quick_replies = ["I need support", "Tell me something positive", "Let's change topic", "Thanks for listening"]
        elif "?" in message:
            quick_replies = ["That helps!", "Tell me more", "Different question", "Thanks!"]
        else:
            # Default contextual replies
            quick_replies = ["Tell me more", "Change topic", "Ask me anything", "That's interesting!"]
        
        return quick_replies[:4]  # Limit to 4 quick replies

# Initialize Bert's brain
bert_brain = BertBrain()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    user_id = data.get('user_id', 'default')
    
    # Process message through Bert's brain
    response, quick_replies = bert_brain.process_message(user_message, user_id)
    
    return jsonify({
        'response': response,
        'quick_replies': quick_replies,
        'timestamp': datetime.now().strftime("%I:%M %p"),
        'message_id': datetime.now().timestamp()
    })

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Determine file type for response
        file_ext = filename.rsplit('.', 1)[1].lower()
        file_type_emoji = {
            'pdf': '📄', 'doc': '📝', 'docx': '📝',
            'png': '🖼️', 'jpg': '🖼️', 'jpeg': '🖼️', 'gif': '🖼️',
            'txt': '📃', 'csv': '📊', 'xlsx': '📊'
        }
        emoji = file_type_emoji.get(file_ext, '📎')
        
        return jsonify({
            'success': True,
            'filename': filename,
            'message': f"{emoji} Perfect! I've received your file '{file.filename}'. I'll process it right away and our team will review it if needed. Is there anything specific you'd like me to help you with regarding this file?"
        })
    
    return jsonify({'error': 'Invalid file type. Allowed types: images, PDFs, documents, spreadsheets.'}), 400

@app.route('/feedback', methods=['POST'])
def feedback():
    data = request.json
    # In production, save this to a database
    print(f"Feedback received: {data}")
    return jsonify({'status': 'success', 'message': 'Thank you for your feedback!'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)