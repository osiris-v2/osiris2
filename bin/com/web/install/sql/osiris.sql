-- Crear la base de datos "osiris"
CREATE DATABASE IF NOT EXISTS osiris_web;

-- Usar la base de datos "osiris"
USE osiris_web;




#Tabla para usuarios 

CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  usr VARCHAR(50) NOT NULL,
  pswd VARCHAR(128) NOT NULL,
  email VARCHAR(100) NOT NULL UNIQUE,
  telefono VARCHAR(20) DEFAULT '000000000',
  fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  perm INT(4) DEFAULT '0'
);





-- Enlazar el archivo "tablas.sql" al final (def dis)
#SOURCE tablas.sql;
