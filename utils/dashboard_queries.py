from utils.db_utils import execute_query, fetch_all

def get_dashboard_statistics():
    """Получить общую статистику для дашборда"""
    query = '''
    SELECT 
        COUNT(*) as total_products,
        SUM(current_quantity) as total_quantity,
        SUM(CASE WHEN current_quantity <= min_quantity THEN 1 ELSE 0 END) as low_stock_count,
        (SELECT COUNT(*) FROM overflow_storage) as overflow_items
    FROM products
    '''
    return fetch_all(query)

def get_critical_products():
    """Получить товары требующие внимания"""
    query = '''
    SELECT p.name, c.name as category, p.current_quantity, p.min_quantity, p.unit
    FROM products p
    JOIN categories c ON p.category_id = c.id
    WHERE p.current_quantity <= p.min_quantity
    '''
    return fetch_all(query)

def get_shelf_occupancy():
    """Получить заполненность стеллажей"""
    query = '''
    SELECT 
        s.name,
        c.name as category,
        s.current_quantity,
        s.max_capacity,
        ROUND((s.current_quantity * 100.0 / s.max_capacity), 2) as fill_percentage
    FROM shelves s
    JOIN categories c ON s.category_id = c.id
    '''
    return fetch_all(query)

def get_recent_notifications():
    """Получить последние уведомления"""
    query = '''
    SELECT type, message, created_date, priority
    FROM notifications 
    WHERE is_read = 0
    ORDER BY 
        CASE priority 
            WHEN 'high' THEN 1
            WHEN 'medium' THEN 2
            ELSE 3
        END,
        created_date DESC
    LIMIT 10
    '''
    return fetch_all(query)

def get_movement_stats():
    """Получить статистику движения товаров за последние 7 дней"""
    query = '''
    SELECT 
        movement_type,
        COUNT(*) as operation_count,
        SUM(quantity) as total_quantity
    FROM movement_history 
    WHERE movement_date >= datetime('now', '-7 days')
    GROUP BY movement_type
    '''
    return fetch_all(query)

# Пример использования
if __name__ == "__main__":
    print("=== Статистика дашборда ===")
    
    stats = get_dashboard_statistics()
    print("Общая статистика:", stats[0] if stats else "Нет данных")
    
    critical = get_critical_products()
    print(f"Критических товаров: {len(critical)}")
    for product in critical:
        print(f"  - {product[0]}: {product[2]}/{product[3]} {product[4]}")
    
    notifications = get_recent_notifications()
    print(f"Непрочитанных уведомлений: {len(notifications)}")
    
    movement = get_movement_stats()
    print("Движение товаров за 7 дней:")
    for move in movement:
        print(f"  - {move[0]}: {move[1]} операций, {move[2]} ед.")