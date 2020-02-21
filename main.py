from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import CoreLabel
from kivy.core.window import Window
from kivy.graphics import Rectangle
from kivy.clock import Clock
import random

class GameWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Request reference to keyboard
        self._keyboard = Window.request_keyboard(self._on_keyboard_close, self)
        self._keyboard.bind(on_key_down=self._on_key_down)
        self._keyboard.bind(on_key_up=self._on_key_up)

        self._score_label = CoreLabel(text="Score: 0", font_size=20)
        self._score_label.refresh()
        self._score = 0

        self.register_event_type("on_frame") # Inherited from super class

        with self.canvas:
            Rectangle(source="assets/background.png", pos=(0,0), size=(Window.width, Window.height))
            self._score_instruction = Rectangle(texture=self._score_label.texture, pos=(10,Window.height - 50), size=self._score_label.texture.size)

        self._keys_pressed = set()
        self._entities = set()

        # Execute move every frame
        Clock.schedule_interval(self._on_frame, 0)

        Clock.schedule_interval(self.spawn_enemies, 1)
    
    def spawn_enemies(self, dt):
        x = random.randint(0, Window.width)
        y = Window.height
        speed = random.randint(100, 200)
        self.add_entity(Enemy((x, y), speed))

    def _on_frame(self, dt):
        self.dispatch("on_frame", dt)

    def on_frame(self, dt):
        pass

    @property
    def score(self):
        return self._score
    
    @score.setter
    def score(self, value):
        self._score = value
        self._score_label.text = "Score: " + str(value)
        self._score_label.refresh()
        self._score_instruction.texture = self._score_label.texture
        self._score_instruction.size = self._score_label.texture.size

    def add_entity(self, entity):
        self._entities.add(entity)
        self.canvas.add(entity._instruction)
    
    def remove_entity(self, entity):
        if entity in self._entities:
            self._entities.remove(entity)
            self.canvas.remove(entity._instruction)

    # Takes two entities as input and returns true if they are colliding
    def collides(self, e1, e2):
        r1_x = e1.pos[0]
        r1_y = e1.pos[1]
        r1_h = e1.size[0]
        r1_w = e1.size[1]

        r2_x = e2.pos[0]
        r2_y = e2.pos[1]
        r2_h = e2.size[0]
        r2_w = e2.size[1]

        if (r1_x < r2_x + r2_w and 
            r1_x + r1_w > r2_x and 
            r1_y < r2_y + r2_h and 
            r1_y + r1_h > r2_y):
            return True
        else:
            return False

    # Returns a set of entities that the given entity collides with
    def colliding_entities(self, entity):
        result = set()
        for e in self._entities:
            if self.collides(e, entity) and e != entity:
                result.add(e)
        return result

    # Unbind from keyboard
    def _on_keyboard_close(self):
        self._keyboard.unbind(on_key_down=self._on_key_down)
        self._keyboard.unbind(on_key_up=self._on_key_up)
        self._keyboard = None
    
    def _on_key_down(self, keyboard, keycode, text, modifiers):
        self._keys_pressed.add(keycode[1])

    def _on_key_up(self, keyboard, keycode):
        text = keycode[1]
        if text in self._keys_pressed:
            self._keys_pressed.remove(text)

class Entity(object):
    def __init__(self):
        self._pos = (0, 0)
        self._size = (50, 50)
        self._instruction = Rectangle(pos=self._pos, size=self._size)
    
    @property
    def pos(self):
        return self._pos
    
    @pos.setter
    def pos(self, value):
        self._pos = value
        self._instruction.pos = self._pos
    
    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        self._size = value
        self._instruction.size = self._size
    
    @property
    def source(self):
        return self._source
    
    @source.setter
    def source(self, value):
        self._source = value
        self._instruction.source = self._source

class Player(Entity):
    def __init__(self):
        super().__init__()
        self._pos = (400, 0)
        self.source = "assets/player.png"
        game.bind(on_frame=self.move_step)
        self._shoot_event = Clock.schedule_interval(self.shoot_step, 0.1)
    
    def stop_callbacks(self):
        game.unbind(on_frame=self.move_step)
        self._shoot_event

    def shoot_step(self, dt):
        if "up" in game._keys_pressed:
            x = self.pos[0] + 20
            y = self.pos[1] + 50
            game.add_entity(Bullet((x, y)))

    def move_step(self, sender, dt):
        step_size = 300 * dt
        x = self.pos[0]
        y = self.pos[1]
        if "left" in game._keys_pressed:
            x -= step_size
        if "right" in game._keys_pressed:
            x += step_size
        self.pos = (x, y)

class Enemy(Entity):
    def __init__(self, pos, speed):
        super().__init__()
        self._speed = speed
        self.pos = pos
        self.source = "assets/enemy.png"
        game.bind(on_frame=self.move_step)
    
    def stop_callbacks(self):
        game.unbind(on_frame=self.move_step)
        
    def move_step(self, sender, dt):
        # Check for out of bounds
        if self.pos[1] < 0:
            # Stop listening to on frame event
            self.stop_callbacks()
            # Remove ourself from canvas
            game.remove_entity(self)
            return
        # Check for collisions
        for e in game.colliding_entities(self):
            if e == game.player:
                game.add_entity(Explosion(self.pos))
                # Stop own callbacks and remove self from game
                self.stop_callbacks()
                game.remove_entity(self)
                return
        # Move
        step_size = self._speed * dt
        new_x = self.pos[0]
        new_y = self.pos[1] - step_size
        self.pos = (new_x, new_y)

class Bullet(Entity):
    def __init__(self, pos, speed=200):
        super().__init__()
        self.pos = pos
        self._speed = speed
        self.size = (9, 37)
        self.source = "assets/bullet.png"
        game.bind(on_frame=self.move_step)
    
    def stop_callbacks(self):
        game.unbind(on_frame=self.move_step)

    def move_step(self, sender, dt):
        # Check for out of bounds
        if self.pos[1] > Window.height:
            # Stop listening to on frame event
            self.stop_callbacks()
            # Remove ourself from canvas
            game.remove_entity(self)
            return
        # Check for collisions
        for e in game.colliding_entities(self):
            # If we collide with an enemy
            if isinstance(e, Enemy):
                game.add_entity(Explosion(e.pos))
                # Stop own callbacks and remove self from game
                self.stop_callbacks()
                game.remove_entity(self)
                # Stop enemy callbacks and remove enemy
                e.stop_callbacks()
                game.remove_entity(e)
                game.score += 1
                return
        # Move
        step_size = self._speed * dt
        new_x = self.pos[0]
        new_y = self.pos[1] + step_size
        self.pos = (new_x, new_y)

class Explosion(Entity):
    def __init__(self, pos):
        super().__init__()
        self.pos = pos
        self.source = "assets/explosion.png"
        Clock.schedule_once(self._remove_me, 0.1)
    
    def _remove_me(self, dt):
        game.remove_entity(self)

game = GameWidget()
game.player = Player()
game.add_entity(game.player)

class MyApp(App):
    def build(self):
        return game

if __name__ == "__main__":
    app = MyApp()
    app.run()