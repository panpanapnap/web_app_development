from .database import get_db_connection

class RegistrationModel:
    @staticmethod
    def create(event_id, student_id, name, phone=None):
        """
        新增一筆記錄 (學生報名活動)。
        包含 Transaction 防止超賣並判斷候補身份。
        
        參數:
            event_id (int): 報名的活動 ID
            student_id (str): 逢甲學號
            name (str): 學生姓名
            phone (str, optional): 聯絡電話
            
        回傳:
            tuple: (registration_id, status)
        """
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("BEGIN TRANSACTION;")
            
            event = cursor.execute('SELECT capacity FROM events WHERE id = ?', (event_id,)).fetchone()
            if not event:
                raise ValueError("活動不存在")
                
            capacity = event['capacity']
            
            current_count_row = cursor.execute('''
                SELECT COUNT(*) as count 
                FROM registrations 
                WHERE event_id = ? AND status = '成功'
            ''', (event_id,)).fetchone()
            
            current_count = current_count_row['count']
            status = '成功' if current_count < capacity else '候補'
            
            cursor.execute('''
                INSERT INTO registrations (event_id, student_id, name, phone, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (event_id, student_id, name, phone, status))
            
            registration_id = cursor.lastrowid
            conn.commit()
            return registration_id, status
            
        except Exception as e:
            conn.rollback()
            print(f"Error in RegistrationModel.create: {e}")
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_all(event_id=None):
        """
        取得所有記錄 (依據活動)。
        
        參數:
            event_id (int, optional): 若有填代表取得特定活動報名表
            
        回傳:
            list[dict]: 報名資料的字典陣列
        """
        conn = get_db_connection()
        try:
            if event_id:
                regs = conn.execute('''
                    SELECT * FROM registrations 
                    WHERE event_id = ? 
                    ORDER BY created_at ASC
                ''', (event_id,)).fetchall()
            else:
                regs = conn.execute('SELECT * FROM registrations ORDER BY created_at ASC').fetchall()
            return [dict(r) for r in regs]
        except Exception as e:
            print(f"Error in RegistrationModel.get_all: {e}")
            return []
        finally:
            conn.close()
            
    @staticmethod
    def get_by_student(student_id):
        """
        取得單一學生的所有報名紀錄。
        
        參數:
            student_id (str): 學號
            
        回傳:
            list[dict]: 紀錄陣列加上關聯的活動標題
        """
        conn = get_db_connection()
        try:
            regs = conn.execute('''
                SELECT registrations.*, events.title as event_title 
                FROM registrations 
                JOIN events ON registrations.event_id = events.id
                WHERE student_id = ? 
                ORDER BY registrations.created_at DESC
            ''', (student_id,)).fetchall()
            return [dict(r) for r in regs]
        except Exception as e:
            print(f"Error in RegistrationModel.get_by_student: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def get_by_id(reg_id):
        """
        取得單筆記錄 (特定報名)。
        
        參數:
            reg_id (int): 報名表 ID
            
        回傳:
            dict: 報名資料，無的話回傳 None
        """
        conn = get_db_connection()
        try:
            reg = conn.execute('SELECT * FROM registrations WHERE id = ?', (reg_id,)).fetchone()
            return dict(reg) if reg else None
        except Exception as e:
            print(f"Error in RegistrationModel.get_by_id: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def update(reg_id, name, phone):
        """
        更新記錄 (聯絡人資訊)。
        
        參數:
            reg_id (int): 報名表 ID
            name (str): 學生姓名
            phone (str): 聯絡電話
        """
        conn = get_db_connection()
        try:
            conn.execute('''
                UPDATE registrations 
                SET name = ?, phone = ?
                WHERE id = ?
            ''', (name, phone, reg_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error in RegistrationModel.update: {e}")
            raise e
        finally:
            conn.close()

    @staticmethod
    def delete(reg_id):
        """
        刪除記錄 (取消報名並自動遞補)。
        
        參數:
            reg_id (int): 欲取消的報名 ID
        """
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("BEGIN TRANSACTION;")
            
            reg = cursor.execute('SELECT event_id, status FROM registrations WHERE id = ?', (reg_id,)).fetchone()
            if not reg:
                raise ValueError("報名紀錄不存在")
                
            event_id = reg['event_id']
            old_status = reg['status']
            
            cursor.execute("UPDATE registrations SET status = '已取消' WHERE id = ?", (reg_id,))
            
            if old_status == '成功':
                next_waitlist = cursor.execute('''
                    SELECT id FROM registrations 
                    WHERE event_id = ? AND status = '候補' 
                    ORDER BY created_at ASC LIMIT 1
                ''', (event_id,)).fetchone()
                
                if next_waitlist:
                    cursor.execute("UPDATE registrations SET status = '成功' WHERE id = ?", (next_waitlist['id'],))
                    
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error in RegistrationModel.delete: {e}")
            raise e
        finally:
            conn.close()
