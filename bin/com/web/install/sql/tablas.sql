#SQL Tables


#Tabla para articulos

CREATE TABLE `edit_files` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT(10) NOT NULL,
  `file_id` VARCHAR(64) NOT NULL UNIQUE,
  `filecode` VARCHAR(128) NOT NULL UNIQUE,
  `format` VARCHAR(6) DEFAULT NULL,
  `title`  VARCHAR(120) NOT NULL,
  `description` VARCHAR(512) DEFAULT NULL,
  `timesave` INT(10),
  `timeupdate` INT(10)
  PRIMARY KEY (`id`)
);
