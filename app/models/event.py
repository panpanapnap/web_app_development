from .database import get_db_connection

class EventModel:
    @staticmethod
    def create(title, capacity, deadline, description=None, location=None):
        """
        新增一筆活動記錄。
        
        參數:
            title (str): 活動標題
            capacity (int): 人數上限
            deadline (str): 報名截止時間
            description (str, optional): 活動描述
            location (str, optional): 地點
            
        回傳:
            int: 新增的活動 ID
        """
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO events (title, description, location, capacity, deadline)
                VALUES (?, ?, ?, ?, ?)
            ''', (title, description, location, capacity, deadline))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            print(f"Error in EventModel.create: {e}")
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_all():
        """
        取得所有活動記錄。
        
        回傳:
            list[dict]: 活動列表的字典陣列
        """
        conn = get_db_connection()
        try:
            events = conn.execute('SELECT * FROM events ORDER BY created_at DESC').fetchall()
            return [dict(e) for e in events]
        except Exception as e:
            print(f"Error in EventModel.get_all: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def get_by_id(event_id):
        """
        取得單筆活動記錄。
        
        參數:
            event_id (int): 活動 ID
            
        回傳:
            dict: 該筆活動資料的字典，若無則回傳 None
        """
        conn = get_db_connection()
        try:
            event = conn.execute('SELECT * FROM events WHERE id = ?', (event_id,)).fetchone()
            return dict(event) if event else None
        except Exception as e:
            print(f"Error in EventModel.get_by_id: {e}")
            return None
        finally:
            conn.close()
        
    @staticmethod
    def update(event_id, title, capacity, deadline, description=None, location=None):
        """
        更新活動記錄。
        
        參數:
            event_id (int): 欲更新的活動 ID
            title (str): 活動標題
            capacity (int): 人數上限
            deadline (str): 報名截止時間
            description (str, optional): 活動描述
            location (str, optional): 地點
        """
        conn = get_db_connection()
        try:
            conn.execute('''
                UPDATE events 
                SET title = ?, description = ?, location = ?, capacity = ?, deadline = ?
                WHERE id = ?
            ''', (title, description, location, capacity, deadline, event_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error in EventModel.update: {e}")
            raise e
        finally:
            conn.close()

    @staticmethod
    def delete(event_id):
        """
        刪除活動記錄。
        
        參數:
            event_id (int): 欲刪除的活動 ID
        """
        conn = get_db_connection()
        try:
            conn.execute('DELETE FROM events WHERE id = ?', (event_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error in EventModel.delete: {e}")
            raise e
        finally:
            conn.close()
