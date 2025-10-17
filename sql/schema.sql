CREATE TABLE unidades_medida (id SERIAL PRIMARY KEY, nombre VARCHAR(50) NOT NULL, factor_base NUMERIC(10,2) DEFAULT 1);

CREATE TABLE productos (id_producto SERIAL PRIMARY KEY, nombre VARCHAR(100) NOT NULL, unidad INT REFERENCES unidades_medida(id), stock NUMERIC(10,2) DEFAULT 0, codigo_softrestaurant VARCHAR(50), familia VARCHAR(50), es_producido BOOLEAN DEFAULT FALSE, es_vendido BOOLEAN DEFAULT TRUE, activo BOOLEAN DEFAULT TRUE);

CREATE TABLE produccion (id_produccion SERIAL PRIMARY KEY, id_producto INT NOT NULL REFERENCES productos(id_producto), fecha DATE NOT NULL DEFAULT CURRENT_DATE, cantidad NUMERIC(10,2) NOT NULL, unidad INT REFERENCES unidades_medida(id), observaciones TEXT);

CREATE TABLE movimientos_inventario (id_movimiento SERIAL PRIMARY KEY, id_producto INT NOT NULL REFERENCES productos(id_producto), fecha DATE NOT NULL DEFAULT CURRENT_DATE, tipo_salida VARCHAR(20) CHECK (tipo_salida IN ('Venta', 'Merma')), cantidad NUMERIC(10,2) NOT NULL, unidad INT REFERENCES unidades_medida(id), observaciones TEXT);

CREATE TABLE ventas (id_venta SERIAL PRIMARY KEY, id_producto INT NOT NULL REFERENCES productos(id_producto), fecha DATE NOT NULL DEFAULT CURRENT_DATE, cantidad NUMERIC(10,2) NOT NULL, precio_unitario NUMERIC(10,2) NOT NULL, descuento NUMERIC(10,2) DEFAULT 0, monto_cobrado NUMERIC(10,2) GENERATED ALWAYS AS ((cantidad * precio_unitario) - descuento) STORED);

CREATE TABLE recetas (id_receta SERIAL PRIMARY KEY, id_producto_final INT NOT NULL REFERENCES productos(id_producto), nombre VARCHAR(100) NOT NULL, version VARCHAR(20), fecha_creacion DATE DEFAULT CURRENT_DATE);

CREATE TABLE detalle_receta (id_detalle SERIAL PRIMARY KEY, id_receta INT NOT NULL REFERENCES recetas(id_receta) ON DELETE CASCADE, id_insumo INT NOT NULL REFERENCES productos(id_producto), cantidad_estimada NUMERIC(10,2) NOT NULL, unidad INT REFERENCES unidades_medida(id));

CREATE TABLE inventario_historico (id_inventario SERIAL PRIMARY KEY, id_producto INT NOT NULL REFERENCES productos(id_producto), fecha DATE NOT NULL DEFAULT CURRENT_DATE, stock_total NUMERIC(10,2), stock_bodega NUMERIC(10,2), stock_vitrina NUMERIC(10,2));

CREATE INDEX idx_productos_nombre ON productos(nombre);
CREATE INDEX idx_ventas_fecha ON ventas(fecha);
CREATE INDEX idx_movimientos_fecha ON movimientos_inventario(fecha);
CREATE INDEX idx_inventario_fecha ON inventario_historico(fecha);

INSERT INTO unidades_medida (nombre, factor_base) VALUES ('Gramo (g)', 1),('Kilogramo (kg)', 1000),('Libra (lb)', 453.592),('Onza (oz)', 28.3495),('Mililitro (ml)', 1),('Litro (L)', 1000),('Galón (gal)', 3785.41),('Onza líquida (oz fl)', 29.5735),('Frasco (200 ml)', 200),('Unidad (pz)', 1),('Docena (12 pz)', 12),('Ciento (100 pz)', 100),('Porción', 1),('Ración (2 porciones)', 2),('Bolsa (350 g)', 350),('Bolsa (120 g)', 120);
