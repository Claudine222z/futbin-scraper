-- Script SQL para limpar posições incorretas
-- Execute este script no seu banco de dados MySQL

-- 1. Primeiro, vamos ver quantas cartas têm posições incorretas
SELECT 
    COUNT(*) as total_cards,
    COUNT(CASE WHEN alt_position_json != '[]' AND alt_position_json != 'null' AND alt_position_json IS NOT NULL THEN 1 END) as cards_with_alt_positions,
    COUNT(CASE WHEN roles_json != '[]' AND roles_json != 'null' AND roles_json IS NOT NULL THEN 1 END) as cards_with_roles
FROM players;

-- 2. Mostrar algumas cartas com posições incorretas (exemplos)
SELECT 
    name, 
    overall, 
    alt_position_json, 
    roles_json
FROM players 
WHERE (alt_position_json != '[]' AND alt_position_json != 'null' AND alt_position_json IS NOT NULL)
   OR (roles_json != '[]' AND roles_json != 'null' AND roles_json IS NOT NULL)
ORDER BY overall DESC
LIMIT 10;

-- 3. LIMPAR TODAS AS POSIÇÕES AUXILIARES E ROLES INCORRETOS
-- ⚠️ ATENÇÃO: Este comando vai limpar TODOS os campos alt_position_json e roles_json
-- Execute apenas se tiver certeza!

UPDATE players 
SET 
    alt_position_json = '[]', 
    roles_json = '[]', 
    updated_at = NOW()
WHERE 
    alt_position_json != '[]' 
    OR roles_json != '[]';

-- 4. Verificar se a limpeza funcionou
SELECT 
    COUNT(*) as total_cards,
    COUNT(CASE WHEN alt_position_json != '[]' AND alt_position_json != 'null' AND alt_position_json IS NOT NULL THEN 1 END) as cards_with_alt_positions,
    COUNT(CASE WHEN roles_json != '[]' AND roles_json != 'null' AND roles_json IS NOT NULL THEN 1 END) as cards_with_roles
FROM players;

-- 5. Verificar algumas cartas após a limpeza
SELECT 
    name, 
    overall, 
    alt_position_json, 
    roles_json
FROM players 
ORDER BY overall DESC
LIMIT 5; 