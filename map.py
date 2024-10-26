import pytmx

def load_map_tmx(file_path):
    # Load the TMX map file using pytmx
    tmx_data = pytmx.TiledMap(file_path)

    tile_grid = []
    
    # get the walls layer
    walls_layer = tmx_data.get_layer_by_name('Walls')

    # fill the tile_grid from the walls layer
    for y in range(tmx_data.height):
        row = []
        for x in range(tmx_data.width):
            # Check if there is a tile at this position (x, y)
            tile = walls_layer.data[y][x]
            if tile:
                row.append(1)  # 1 = Wall
            else:
                row.append(0)  # 0 = Empty space
        tile_grid.append(row)

    return tile_grid

