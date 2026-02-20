# Solución al Problema de Duplicación del Módulo

## Problema Identificado

Después de ejecutar la migración en Odoo.sh, se observa que:
- ✗ El módulo `commission_oca` está instalado correctamente
- ✗ El módulo antiguo `commission` sigue apareciendo como instalado
- ✗ Los identificadores externos (XML IDs) de `commission` no se eliminaron

## Causa

El problema puede ocurrir si:
1. La función `util.rename_module()` no completó la limpieza totalmente
2. Hay referencias circulares o dependencias que impiden la limpieza
3. El proceso se interrumpió antes de completar

## Solución Inmediata

### Opción 1: Ejecutar el script end-cleanup.py

Los scripts han sido actualizados con un nuevo archivo `end-cleanup.py` que se ejecuta en la fase `end` (después de que todos los módulos se cargan). Este script:

1. **Elimina completamente** el módulo `commission` de `ir_module_module`
2. **Limpia XML IDs duplicados** o los migra si son huérfanos
3. **Actualiza dependencias** de otros módulos
4. **Verifica** que todo esté correcto

**Para activarlo en Odoo.sh:**
```bash
# Simplemente actualiza el módulo commission_oca
# El script end-cleanup.py se ejecutará automáticamente
```

### Opción 2: Script SQL Manual (si end-cleanup no es suficiente)

Si necesitas limpiar manualmente, ejecuta estos comandos SQL en el shell de Odoo.sh:

```python
# Accede al shell de Odoo
# En Odoo.sh: Acceso > Shell > Python

env = api.Environment(cr, SUPERUSER_ID, {})

# 1. Eliminar módulo antiguo 'commission'
cr.execute("""
    DELETE FROM ir_module_module_dependency 
    WHERE name = 'commission' OR module_id IN (
        SELECT id FROM ir_module_module WHERE name = 'commission'
    )
""")
print(f"Dependencies removed: {cr.rowcount}")

cr.execute("DELETE FROM ir_module_module WHERE name = 'commission'")
print(f"Old module removed: {cr.rowcount}")

# 2. Limpiar XML IDs duplicados
cr.execute("""
    WITH duplicates AS (
        SELECT old.id as old_id, new.id as new_id
        FROM ir_model_data old
        INNER JOIN ir_model_data new 
            ON old.name = new.name 
            AND old.model = new.model
            AND old.res_id = new.res_id
        WHERE old.module = 'commission' 
        AND new.module = 'commission_oca'
    )
    DELETE FROM ir_model_data 
    WHERE id IN (SELECT old_id FROM duplicates)
""")
print(f"Duplicate XML IDs removed: {cr.rowcount}")

# 3. Migrar XML IDs huérfanos
cr.execute("""
    UPDATE ir_model_data 
    SET module = 'commission_oca'
    WHERE module = 'commission'
    AND NOT EXISTS (
        SELECT 1 FROM ir_model_data new
        WHERE new.module = 'commission_oca'
        AND new.name = ir_model_data.name
        AND new.model = ir_model_data.model
    )
""")
print(f"Orphaned XML IDs migrated: {cr.rowcount}")

# 4. Actualizar dependencias
cr.execute("""
    UPDATE ir_module_module_dependency
    SET name = 'commission_oca'
    WHERE name = 'commission'
""")
print(f"Dependencies updated: {cr.rowcount}")

# 5. Commit
env.cr.commit()
print("✓ Cleanup completed!")

# 6. Verificar
cr.execute("SELECT COUNT(*) FROM ir_module_module WHERE name = 'commission'")
print(f"Old modules remaining: {cr.fetchone()[0]} (should be 0)")

cr.execute("SELECT COUNT(*) FROM ir_model_data WHERE module = 'commission'")
print(f"Old XML IDs remaining: {cr.fetchone()[0]} (should be 0)")

cr.execute("SELECT COUNT(*) FROM ir_model_data WHERE module = 'commission_oca'")
print(f"New XML IDs: {cr.fetchone()[0]}")
```

### Opción 3: Forzar actualización con scripts mejorados

1. Los scripts `pre-migration.py`, `post-migration.py` y `end-cleanup.py` han sido mejorados
2. Para forzar su re-ejecución:

```bash
# En Odoo.sh, actualiza la versión del módulo
# Edita __manifest__.py y cambia:
# "version": "18.0.1.0.2" → "version": "18.0.1.0.3"

# Luego actualiza el módulo commission_oca
```

## Verificación Post-Limpieza

Ejecuta estas queries para verificar que todo está correcto:

```sql
-- 1. No debe existir módulo 'commission'
SELECT name, state 
FROM ir_module_module 
WHERE name = 'commission';
-- Resultado esperado: 0 filas

-- 2. Debe existir módulo 'commission_oca' instalado
SELECT name, state 
FROM ir_module_module 
WHERE name = 'commission_oca';
-- Resultado esperado: 1 fila con state = 'installed'

-- 3. No deben existir XML IDs con módulo 'commission'
SELECT COUNT(*) 
FROM ir_model_data 
WHERE module = 'commission';
-- Resultado esperado: 0

-- 4. Deben existir XML IDs con módulo 'commission_oca'
SELECT COUNT(*) 
FROM ir_model_data 
WHERE module = 'commission_oca';
-- Resultado esperado: > 0 (al menos 50+)

-- 5. Verificar dependencias
SELECT m.name 
FROM ir_module_module m
JOIN ir_module_module_dependency d ON d.module_id = m.id
WHERE d.name = 'commission';
-- Resultado esperado: 0 filas

-- 6. Módulos que dependen correctamente de commission_oca
SELECT m.name 
FROM ir_module_module m
JOIN ir_module_module_dependency d ON d.module_id = m.id
WHERE d.name = 'commission_oca';
-- Resultado esperado: account_commission_oca, sale_commission_oca, etc.
```

## Prevención Futura

Los scripts actualizados ahora incluyen:

1. **Verificación previa**: Comprueba el estado antes de actuar
2. **Limpieza agresiva**: Elimina activamente duplicados
3. **Migración de huérfanos**: Migra XML IDs que no tienen duplicado
4. **Verificación final**: Confirma que todo está limpio
5. **Logging detallado**: Registra cada acción para debugging

## Orden de Ejecución de Scripts

```
1. pre-migration.py     → Renombra y limpia (ANTES de cargar)
2. [Carga módulo]       → Odoo carga commission_oca
3. post-migration.py    → Verifica y limpia más (DESPUÉS de cargar)
4. [Cargan otros mods]  → Se cargan módulos dependientes
5. end-cleanup.py       → Limpieza final y verificación (FINAL)
```

## Contacto

Si después de aplicar estas soluciones el problema persiste:
1. Revisa los logs de Odoo.sh para mensajes de error
2. Ejecuta las queries de verificación
3. Proporciona los resultados para análisis adicional

## Notas Importantes

- ⚠️ **Siempre haz backup** antes de ejecutar scripts SQL manuales
- ✓ Los scripts automáticos (end-cleanup.py) son la opción más segura
- ✓ La opción SQL manual es para casos donde los scripts automáticos no funcionaron
- ✓ Después de la limpieza, verifica que los módulos dependientes funcionen correctamente
