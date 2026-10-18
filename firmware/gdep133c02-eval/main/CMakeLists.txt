idf_component_register(SRCS "main.c" "board.c" INCLUDE_DIRS "." REQUIRES epd esp_driver_gpio esp_driver_spi esp_timer console esp_psram EMBED_FILES "../assets/photo.epf")
