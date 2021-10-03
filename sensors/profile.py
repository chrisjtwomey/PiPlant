
PROFILE_SUCCULENT           = 0
PROFILE_CHINA_DOLL_BONSAI   = 1
PROFILE_FUKIEN_TEA_BONSAI   = 2
PROFILE_PALM                = 3
PROFILE_FICUS               = 4
PROFILE_DEFAULT             = 5

class PlantCareProfile:
    
    def __init__(self, profile):
        self.needs_water_threshold_percent = 20
        self.temp_min_c = 8
        self.temp_max_c = 28
        self.icon = 'plant.png'
        
        if profile == PROFILE_SUCCULENT:
            self.needs_water_threshold_percent = 0 # let soil dry out
            self.temp_min_c = 11
            self.temp_max_c = 28
            self.icon = 'succulent.png'

        if profile == PROFILE_CHINA_DOLL_BONSAI:
            self.needs_water_threshold_percent = 50
            self.temp_min_c = 5
            self.temp_max_c = 25.5
            self.icon = 'china_doll.png'

        if profile == PROFILE_FUKIEN_TEA_BONSAI:
            self.needs_water_threshold_percent = 50
            self.temp_min_c = 5
            self.temp_max_c = 25.5
            self.icon = 'fukien_tea.png'

        if profile == PROFILE_PALM:
            self.needs_water_threshold_percent = 20
            self.temp_min_c = 7
            self.temp_max_c = 28
            self.icon = 'palm.png'

        if profile == PROFILE_FICUS:
            self.needs_water_threshold_percent = 20
            self.temp_min_c = 10
            self.temp_max_c = 27
            self.icon = 'ficus.png'

    def needs_water(self, val_percent):
        return val_percent <= self.needs_water_threshold_percent