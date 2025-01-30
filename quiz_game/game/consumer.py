import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils.crypto import get_random_string




class QuizConsumer(AsyncWebsocketConsumer):
    rooms = {}  # In-memory storage for rooms (consider using database for production)

    async def connect(self):
        self.room_code = None
        self.user = self.scope["user"]

        
        print(self.user)
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
                'score': 0
            }],
            'leader': self.user.username,
            'game_started': False,
            'current_question': None,
        }

        await self.channel_layer.group_add(
            self.room_code,
            self.channel_name
        )

        await self.send(text_data=json.dumps({
            'type': 'room_created',
            'room_code': room_code,
            'room': self.rooms[room_code]
        }))

    async def join_room(self, data):
        room_code = data['room_code'].upper()
        username = self.user.username

        if room_code not in self.rooms:
            await self.send(json.dumps({
                'type': 'error',
                'message': 'Room not found'
            }))
            return

        room = self.rooms[room_code]
        if len(room['players']) >= 8:  # Example max players
            await self.send(json.dumps({
                'type': 'error',
                'message': 'Room is full'
            }))
            return

        self.room_code = room_code
        room['players'].append({
            'user': username,
            'ready': False,
            'leader': False,
            'answered':False,
            'score': 0
        })

        await self.channel_layer.group_add(
            self.room_code,
            self.channel_name
        )

        await self.channel_layer.group_send(
            self.room_code,
            {
                'type': 'player_joined',
                'room_code': room_code,
                'room': room
            }
        )

    async def toggle_ready(self):
        room = self.rooms[self.room_code]
        player = next(p for p in room['players'] if p['user'] == self.user.username)
        player['ready'] = True
        print('player has readied up')
        await self.channel_layer.group_send(
            self.room_code,
            {
                'type': 'player_status',
                'players': room['players']
            }
        )

    async def start_game(self):
        room = self.rooms[self.room_code]
        player = next(p for p in room['players'] if p['user'] == self.user.username)
        
        if not player['leader']:
            await self.send(json.dumps({
                'type': 'error',
                'message': 'Only leader can start the game'
            }))
            return
        
        print(player['leader'])
        if not all(p['ready'] for p in room['players']):
            await self.send(json.dumps({
                'type': 'error',
                'message': 'Not all players are ready'
            }))
            return

        room['game_started'] = True
        # Here you would typically load questions from your database
        await self.send_next_question()

    async def send_next_question(self):
        print('ive reached the question part')
        room = self.rooms[self.room_code]
        # Replace with actual question loading logic
        question = {
            'text': "What is 2+2?",
            'options': ["3", "4", "5"],
            'correct_answer': 1
        }
        room['current_question'] = question

        await self.channel_layer.group_send(
            self.room_code,
            {
                'type': 'new_question',
                'question': question
            }
        )

    async def handle_answer(self, data):
        room = self.rooms[self.room_code]
        player = next(p for p in room['players'] if p['user'] == self.user.username)
        print("answer recieved" )
        player['answered'] = not player['answered']
        await self.send(text_data=json.dumps({
                'type': 'answer_recieved',
            }))
        
        # Add answer validation and scoring logic here
        if data['answer'] == room['current_question']['correct_answer']:
            player['score'] += 10
        if not all(p['answered'] for p in room['players']):
            
            return
        for player in room["players"]:
            player["answered"] = False

        ####check_results()
        await self.channel_layer.group_send(
            self.room_code,
            {
                'type': 'update_scores',
                'players': room['players'],
                'leader' : room['leader'],
                'room_code': self.room_code
            }
        )

    async def leave_room(self):
        

        room = self.rooms[self.room_code]
        room['players'] = [p for p in room['players'] if p['user'] != self.user.username]
        await self.channel_layer.group_discard(
            self.room_code,
            self.channel_name
            
        )
        await self.send(text_data=json.dumps({
                'type': 'player_disconnected',
            }))
        if not room['players']:
            del self.rooms[self.room_code]
        else:
            # If leader leaves, assign new leader
            if not any(p['leader'] for p in room['players']):
                room['players'][0]['leader'] = True
                leader=room['players'][0]
            print(room['players'])
            await self.channel_layer.group_send(
                
                self.room_code,
                {
                    'type': 'player_left',
                    'players': room['players'],
                    'leader': leader
                }
            )

    # Handler methods
    async def player_joined(self, event):
        await self.send(text_data=json.dumps(event))

    async def player_status(self, event):
        await self.send(text_data=json.dumps(event))

    async def new_question(self, event):
        await self.send(text_data=json.dumps(event))

    async def update_scores(self, event):
        await self.send(text_data=json.dumps(event))

    async def player_left(self, event):
        await self.send(text_data=json.dumps(event))
