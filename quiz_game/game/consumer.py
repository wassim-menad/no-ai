import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils.crypto import get_random_string




class QuizConsumer(AsyncWebsocketConsumer):
    rooms = {}  # In-memory storage for rooms (consider using database for production)

    async def connect(self):
        self.room_code = None
        self.question_index = 0
        self.user = self.scope["user"]

        
        
        await self.accept()

    
    async def disconnect(self, close_code):
        if self.room_code:
            await self.leave_room()

    
    async def receive(self, text_data):
        data = json.loads(text_data)
        command = data.get('command')

        if command == 'create':
            await self.create_room(data)
        elif command == 'join':
            await self.join_room(data)
        elif command == 'ready':
            await self.toggle_ready()
        elif command == 'start':
            await self.toggle_ready()
            await self.start_game()
        elif command == 'answer':
            await self.handle_answer(data)
        elif command == 'leave':
            await self.leave_room()
        elif command == 'next':
            await self.send_next_question()

    
    async def create_room(self, data):
        # Generate unique room code
        room_code = get_random_string(6).upper()
        while room_code in self.rooms:
            room_code = get_random_string(6).upper()

        self.room_code = room_code
        self.rooms[room_code] = {
            'players': [{
                'user': self.user.username,
                'ready': False,
                'leader': True,
                'answered':False,
                'answers':[],
                'score': 0,
                'color': '#FFEEAD',
            }],
            'leader_user': self.user.username,
            'game_started': False,
            'question': None,
            'round_number': 0,
            'code':room_code
        }

        await self.channel_layer.group_add(
            self.room_code,
            self.channel_name
        )
        await self.propagate_room_event('room_created')
        
    
    async def join_room(self, data):
        room_code = data['room_code'].upper()
        username = self.user.username
        
        if room_code not in self.rooms:
            await self.errortUpdate('Room not found')
            
            return

        room = self.rooms[room_code]
        if len(room['players']) >= 8:  # Example max players
            await self.errortUpdate('Room is full')
            
            return
        color = self.generate_unique_color()
        self.room_code = room_code
        room['players'].append({
            'user': username,
            'ready': False,
            'leader': False,
            'answered':False,
            'answers':[],
            'score': 0,
            'color':color
        })
        
        
        await self.channel_layer.group_add(
            self.room_code,
            self.channel_name
        )
        await self.propagate_room_event('player_joined')

    
    async def toggle_ready(self):
        room = self.rooms[self.room_code]
        player = next(p for p in room['players'] if p['user'] == self.user.username)
        player['ready'] = not player['ready']
        if(player['leader']):
            player['ready'] = True
        
        await self.propagate_room_event('player_status')

    
    async def start_game(self):
        room = self.rooms[self.room_code]
        room['round_number'] = 0
        player = next(p for p in room['players'] if p['user'] == self.user.username)
        
        if not player['leader']:
            await self.errortUpdate('Only leader can start the game')
            
            return
        
        
        if not all(p['ready'] for p in room['players']):
            await self.errortUpdate('Not all players are ready')
            
            return

        room['game_started'] = True

        
        await self.send_first_next_question()

    
    async def getQuestions(self):
        room = self.rooms[self.room_code]
        questions = [
            {
                "text": "What is 2+2?",
                "options": ["3", "4", "5"],
                "correct_answer": 1
            },
            {
                "text": "What is the capital of France?",
                "options": ["Berlin", "Madrid", "Paris"],
                "correct_answer": 2
            },
                {
                "text": "Which planet is known as the Red Planet?",
                "options": ["Earth", "Mars", "Jupiter"],
                "correct_answer": 1
            },
            {
                "text": "How many continents are there?",
                "options": ["5", "6", "7"],
                "correct_answer": 2
            },
            {
                "text": "What is the square root of 16?",
                "options": ["2", "4", "8"],
                "correct_answer": 1
            },
            {
                "text": "Who wrote 'Hamlet'?",
                "options": ["Shakespeare", "Hemingway", "Tolstoy"],
                "correct_answer": 0
            },
            {
                "text": "Which gas do plants absorb from the atmosphere?",
                "options": ["Oxygen", "Nitrogen", "Carbon Dioxide"],
                "correct_answer": 2
            },
            {
                "text": "What is the largest ocean on Earth?",
                "options": ["Atlantic", "Indian", "Pacific"],
                "correct_answer": 2
            },
            {
                "text": "How many legs does a spider have?",
                "options": ["6", "8", "10"],
                "correct_answer": 1
            },
            {
                "text": "What is the boiling point of water?",
                "options": ["90°C", "100°C", "110°C"],
                "correct_answer": 1
            }
        ]
        
        if room['round_number'] < len(questions):  # Check if questions are available
            room['question'] = questions[room['round_number']]
            room['round_number'] += 1  # Move to the next question
   
            
            
            return room['question']
            
        else:
                await self.gameEnd(room)
                return
    
    
    async def send_next_question(self):

        self.rooms[self.room_code]['question']=await self.getQuestions()
        
        if(self.rooms[self.room_code]['question']):
           
       
            await self.propagate_room_event('new_question')

    
    async def send_first_next_question(self):
        

 
        self.rooms[self.room_code]['question']=await self.getQuestions()
        
        if(self.rooms[self.room_code]['question']):
            
  
            await self.propagate_room_event('game_started')

    
    async def handle_answer(self, data):

        room = self.rooms[self.room_code]
        player = next(p for p in room['players'] if p['user'] == self.user.username)

        player['answers'].append(data['answer'])
        player['answered'] = True
        await self.propagate_room_event('answer_recieved')

        
    
        # Add answer validation and scoring logic here
        if data['answer'] == room['question']['correct_answer']:
            player['score'] += 10
        if(True):
            if  all(p['answered'] for p in room['players']):
              
                for player in room["players"]:
                    player["answered"] = False
                await self.propagate_room_event('scores')


    async def checkReady(self,room):
        if  all(p['answered'] for p in room['players']):
        
                for player in room["players"]:
                    player["answered"] = False
                await self.send_next_question(room)
    
    
    async def gameEnd(self,room):

        await self.propagate_room_event('update_scores')

        
    async def leave_room(self):

        room = self.rooms[self.room_code]
        room['players'] = [p for p in room['players'] if p['user'] != self.user.username]
        await self.channel_layer.group_discard(
            self.room_code,
            self.channel_name
        )
        await self.requestUpdate('player_disconnected')
        
        if not room['players']:
            del self.rooms[self.room_code]
        else:
            # If leader leaves, assign new leader
            if not any(p['leader'] for p in room['players']):
                room['players'][0]['leader'] = True
                room['leader_user']=room['players'][0]['user']
      
            await self.propagate_room_event('player_left')


    ##### NEW LOGIC
    async def propagate_room_event(self,message):
        
     
        await self.channel_layer.group_send(
            self.room_code,
            {
                'type': 'handle_room_broadcast',
                'event_type': message,
            }
        )
    
    
    async def handle_room_broadcast(self,event):
        await self.send(text_data=json.dumps({
                'type': event['event_type'],
                'info': self.rooms[self.room_code]
            }))
        
    
    async def requestUpdate(self,message):
        await self.send(text_data=json.dumps({
                'type': message
            }))
    
    
    async def errortUpdate(self,message):
        await self.send(text_data=json.dumps({
                'type': 'error',
                'message' : message
            }))

    def generate_unique_color(self):
        # Use a predefined palette for better consistency
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FF9F76']
        return get_random_string(1, allowed_chars=colors)