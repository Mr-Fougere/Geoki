from pyproj import Proj, transform

class PositionConverter:
    def __init__(self, input_projection='epsg:4326', output_projection='epsg:3857'):
        self.input_projection = Proj(init=input_projection)
        self.output_projection = Proj(init=output_projection)
    
    def convert_lat_lon_to_xy(self, lon, lat):
        x, y = transform(self.input_projection, self.output_projection, lon, lat)
        return x, y

    def convert_xy_to_lat_lon(self, x, y):
        lon, lat = transform(self.output_projection, self.input_projection, x, y)
        return lon, lat