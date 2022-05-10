import ntpath
import pygame
from mlgame.gamedev.game_interface import PaiaGame, GameStatus
from mlgame.view.test_decorator import check_game_result
from mlgame.view.view_model import create_text_view_data, create_asset_init_data, create_image_view_data, \
    Scene, create_rect_view_data
from .BattleMode import BattleMode
from .sound_controller import *

'''need some fuction same as arkanoid which without dash in the name of fuction'''


class TankMan(PaiaGame):
    def __init__(self, map_no: int, time_limit: int, sound: str):
        super().__init__()
        self.scene = Scene(WIDTH, HEIGHT, BLACK)
        self.map_path = path.join(MAP_DIR, f"map_0{map_no}.tmx")
        self.time_limit = time_limit
        if sound == "on":
            self.is_sound = True
        else:
            self.is_sound = False
        self.game_mode = self.set_game_mode()
        self.attachements = []

    def game_to_player_data(self) -> dict:
        scene_info = self.get_scene_info
        to_player_data = {}
        for player in self.game_mode.players:
            player_data = player.get_info()
            player_data["frame"] = scene_info["frame"]
            player_data["status"] = scene_info["status"]
            player_data["mobs_pos"] = []
            player_data["walls_xy"] = []

            for wall in self.game_mode.walls:
                player_data["walls_xy"].append(wall.get_pos_xy())

            to_player_data[player_data['player_id']] = player_data

        if to_player_data:
            return to_player_data
        else:
            return {
                "1P": scene_info,
                "2P": scene_info,
                "3P": scene_info,
                "4P": scene_info
            }

    @property
    def get_scene_info(self):
        """
        Get the scene information
        """
        scene_info = {'frame': self.game_mode.used_frame,
                      'status': self.game_mode.status,
                      'background': [WIDTH, HEIGHT],
                      'walls_xy': [],
                      'game_result': self.game_mode.get_result(),
                      'state': self.game_mode.state}

        for player in self.game_mode.players:
            scene_info[f"{player._no}P_xy"] = player.get_pos_xy()
        for wall in self.game_mode.walls:
            scene_info["walls_xy"].append(wall.get_pos_xy())
        return scene_info

    def update(self, commands: dict):
        self.frame_count += 1
        self.game_mode.update(commands)
        if not self.is_running():
            self.rank()
            return "RESET"

    def reset(self):
        self.frame_count = 0
        self.game_mode = self.set_game_mode()
        self.rank()
        # self.game_mode.sound_controller.player_music()

    def is_running(self):
        if self.game_mode.status == GameStatus.GAME_ALIVE:
            return True
        else:
            return False

    def get_scene_init_data(self) -> dict:
        """
        Get the scene and object information for drawing on the web
        """
        game_info = {'scene': self.scene.__dict__,
                     'assets': []}

        # initialize bullets image
        game_info["assets"].append(create_asset_init_data("bullets", TILE_X_SIZE, TILE_Y_SIZE
                                                          , BULLET_IMG_PATH, ""))
        # initialize player image
        for player in self.game_mode.players:
            game_info['assets'].append(create_asset_init_data(f'{player._no}P', player.get_origin_size()[0], player.get_origin_size()[1]
                                                              , player.img_path, ""))
        # initialize bullet stations image
        for bullet_station in self.game_mode.bullet_stations:
            c = 0
            for img_path in BULLET_STATION_IMG_PATH_LIST:
                c += 1
                game_info['assets'].append(create_asset_init_data(f'{bullet_station._no}_{c}', bullet_station.get_size()[0], bullet_station.get_size()[1]
                                                                  , img_path, ""))
        # initialize oil stations image
        for oil_station in self.game_mode.oil_stations:
            c = 0
            for img_path in OIL_STATION_IMG_PATH_LIST:
                c += 1
                game_info['assets'].append(create_asset_init_data(f'{oil_station._no}_{c}', oil_station.get_size()[0], oil_station.get_size()[1]
                                                                  , img_path, ""))
        # initialize walls image
        for wall in self.game_mode.walls:
            c = 0
            for img_path in WALL_IMG_PATH_LIST:
                game_info["assets"].append(create_asset_init_data(f"wall_{wall._no}_{wall.lives-c}", wall.get_size()[0], wall.get_size()[1]
                                                                  , img_path, ""))
                c += 1

        return game_info

    # @check_game_progress
    def get_scene_progress_data(self) -> dict:
        """
        Get the position of src objects for drawing on the web
        """

        game_progress = {'background': [],
                         'object_list': [],
                         'toggle': [],
                         'foreground': [],
                         'user_info': [],
                         'game_sys_info': {}}

        # update bullet image
        for bullet in self.game_mode.bullets:
            bullet_obj = create_image_view_data('bullets', bullet.rect.x, bullet.rect.y,
                                                bullet.rect.width, bullet.rect.height, bullet.angle)
            game_progress["object_list"].append(bullet_obj)
        # update bullet stations image
        for bullet_station in self.game_mode.bullet_stations:
            if bullet_station.power < bullet_station.capacity // 3:
                no = 1
            elif bullet_station.power != bullet_station.capacity:
                no = 2
            else:
                no = 3
            game_progress["object_list"].append(create_image_view_data(f"{bullet_station._no}_{no}",
                                                                       bullet_station.get_pos_xy()[0],
                                                                       bullet_station.get_pos_xy()[1],
                                                                       bullet_station.get_size()[0],
                                                                       bullet_station.get_size()[1]))
        # update oil stations image
        for oil_station in self.game_mode.oil_stations:
            if oil_station.power < oil_station.capacity // 3:
                no = 1
            elif oil_station.power != oil_station.capacity:
                no = 2
            else:
                no = 3
            game_progress["object_list"].append(create_image_view_data(f"{oil_station._no}_{no}",
                                                                       oil_station.get_pos_xy()[0],
                                                                       oil_station.get_pos_xy()[1],
                                                                       oil_station.get_size()[0],
                                                                       oil_station.get_size()[1]))
        # update player image
        for player in self.game_mode.players:
            player_obj = create_image_view_data(f'{player._no}P', player.get_pos_xy()[0], player.get_pos_xy()[1],
                                                player.get_origin_size()[0], player.get_origin_size()[1], player.angle)
            game_progress["object_list"].append(player_obj)
        # update walls image
        for wall in self.game_mode.walls:
            if wall.lives == 0:
                continue
            game_progress["object_list"].append(create_image_view_data(f'wall_{wall._no}_{wall.lives}', wall.rect.x, wall.rect.y,
                                                                       TILE_X_SIZE, TILE_Y_SIZE))
        # update 1P score text
        game_progress["foreground"].append(create_text_view_data(f"1P_Score: {self.game_mode.player_1P.score}",
                                                                 WIDTH / 2 - 30, 0, WHITE, "20px Arial"))
        # update 1P score text
        game_progress["foreground"].append(create_text_view_data(f"2P_Score: {self.game_mode.player_2P.score}",
                                                                 WIDTH / 2 - 30, HEIGHT - 25, WHITE, "20px Arial"))
        # update frame text
        game_progress["foreground"].append(create_text_view_data(f"Time: {(self.game_mode.used_frame // 60)}",
                                                                 WIDTH - 90, 0, WHITE, "20px Arial"))
        # update 1P lives text
        game_progress["foreground"].append(create_text_view_data(f"Shield: {self.game_mode.player_1P.shield}",
                                                                 WIDTH - 90, HEIGHT - 25, WHITE, "20px Arial"))
        # update 2P lives text
        game_progress["foreground"].append(create_text_view_data(f"2P Shield: {self.game_mode.player_2P.shield},",
                                                                 5, HEIGHT - 25, WHITE, "20px Arial"))
        # update 1P powers text
        game_progress["foreground"].append(create_text_view_data(f"Power: {self.game_mode.player_1P.power},",
                                                                 WIDTH - 180, HEIGHT - 25, WHITE, "20px Arial"))
        # update 2P powers text
        game_progress["foreground"].append(create_text_view_data(f"Power: {self.game_mode.player_2P.power},",
                                                                 130, HEIGHT - 25, WHITE, "20px Arial"))
        # update 1P oil text
        game_progress["foreground"].append(create_text_view_data(f"1P Oil: {self.game_mode.player_1P.oil},",
                                                                 WIDTH - 280, HEIGHT - 25, WHITE, "20px Arial"))
        # update 2P oil text
        game_progress["foreground"].append(create_text_view_data(f"Oil: {self.game_mode.player_2P.oil}",
                                                                 220, HEIGHT - 25, WHITE, "20px Arial"))

        return game_progress

    @check_game_result
    def get_game_result(self):
        """
        Get the src result for the web
        """

        return {"frame_used": self.frame_count,
                "state": self.game_result_state,
                "attachment": self.rank()
                }

    def get_keyboard_command(self):
        """
        Get the command according to the pressed keys
        """
        # TODO 此處回傳的資料 要與 ml_play.py 一致
        cmd_1P = ""
        cmd_2P = ""
        cmd_3P = ""
        cmd_4P = ""

        key_pressed_list = pygame.key.get_pressed()
        if key_pressed_list[pygame.K_UP]:
            cmd_1P = FORWARD_CMD
        elif key_pressed_list[pygame.K_DOWN]:
            cmd_1P = BACKWARD_CMD

        if key_pressed_list[pygame.K_w]:
            cmd_2P = FORWARD_CMD
        elif key_pressed_list[pygame.K_s]:
            cmd_2P = BACKWARD_CMD

        if key_pressed_list[pygame.K_SPACE]:
            cmd_1P = SHOOT
        if key_pressed_list[pygame.K_f]:
            cmd_2P = SHOOT

        for even in pygame.event.get():
            if even.type == pygame.KEYDOWN:
                if even.key == pygame.K_RIGHT:
                    cmd_1P = RIGHT_CMD
                elif even.key == pygame.K_LEFT:
                    cmd_1P = LEFT_CMD

                if even.key == pygame.K_d:
                    cmd_2P = RIGHT_CMD
                elif even.key == pygame.K_a:
                    cmd_2P = LEFT_CMD

        if not self.is_running():
            return {"1P": "RESET",
                    "2P": "RESET",
                    "3P": "RESET",
                    "4P": "RESET",
                    }

        return {"1P": cmd_1P,
                "2P": cmd_2P,
                "3P": cmd_3P,
                "4P": cmd_4P,
                }

    @staticmethod
    def ai_clients():
        """
        let MLGame know how to parse your ai,
        you can also use this names to get different cmd and send different data to each ai client
        """
        return [
            {"name": "1P"},
            {"name": "2P"},
            {"name": "3P"},
            {"name": "4P"}
        ]

    def set_game_mode(self):
        game_mode = BattleMode(self.map_path, self.time_limit, self.is_sound)
        return game_mode

    def rank(self):
        self.game_result_state = self.game_mode.state
        game_result = self.game_mode.get_result()
        self.attachements = game_result
        return self.attachements
