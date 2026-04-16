from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from app.models.event import EventModel
from app.models.registration import RegistrationModel

registrations_bp = Blueprint('registrations', __name__)

@registrations_bp.route('/events/<int:event_id>/registrations', methods=['GET'])
def manage_registrations(event_id):
    """
    主辦方用：顯示特定活動的所有成功/候補名單列表
    - 驗證該活動的存在性
    - 模板：registrations/manage.html
    """
    event = EventModel.get_by_id(event_id)
    if not event:
        abort(404)
        
    regs = RegistrationModel.get_all(event_id=event_id)
    return render_template('registrations/manage.html', event=event, registrations=regs)

@registrations_bp.route('/events/<int:event_id>/register', methods=['GET'])
def register_page(event_id):
    """
    逢甲學生用：顯示線上填寫學號與資料表單頁面
    - 事前阻絕逾時的報名行為
    - 模板：registrations/new.html
    """
    event = EventModel.get_by_id(event_id)
    if not event:
        abort(404)
        
    return render_template('registrations/new.html', event=event)

@registrations_bp.route('/events/<int:event_id>/register', methods=['POST'])
def register(event_id):
    """
    逢甲學生用：送出活動參與報名
    - 核心：執行嚴格的 Transaction 機制來判斷有無剩餘名額以防止超賣
    - 判定最終應處在「成功」或「候補」隊伍，再進行通知訊息派送
    - 重導向至個人的履歷狀態
    """
    student_id = request.form.get('student_id')
    name = request.form.get('name')
    phone = request.form.get('phone', '')
    
    if not student_id or not name:
        flash('學號與姓名為必填項目', 'error')
        return redirect(url_for('registrations.register_page', event_id=event_id))
        
    try:
        reg_id, status = RegistrationModel.create(event_id, student_id, name, phone)
        if status == '成功':
            flash(f'恭喜報名成功！您的報名序號為：{reg_id}', 'success')
        else:
            flash(f'非常抱歉，本次活動名額已滿，您已自動排入候補名單！', 'warning')
        
        # 導向到學生的歷史清單頁，並帶入 student_id 參數顯示
        return redirect(url_for('registrations.my_registrations', student_id=student_id))
    except Exception as e:
        flash(f'發生內部錯誤：{str(e)}', 'error')
        return redirect(url_for('registrations.register_page', event_id=event_id))

@registrations_bp.route('/my/registrations', methods=['GET'])
def my_registrations():
    """
    逢甲學生用：總覽自己填過表單的所有足跡清單
    - 搭配網址附上學號拉出特定清單 (MVP使用Query String登入)
    - 模板：registrations/my_list.html
    """
    student_id = request.args.get('student_id')
    if not student_id:
        # 設計一個空白頁要求輸入學號
        return render_template('registrations/my_list.html', student_id=None, registrations=[])
        
    regs = RegistrationModel.get_by_student(student_id)
    return render_template('registrations/my_list.html', student_id=student_id, registrations=regs)

@registrations_bp.route('/registrations/<int:reg_id>/update', methods=['POST'])
def update_registration(reg_id):
    """
    逢甲學生用：局部更新已送出的報名聯絡電話與資訊
    - 不調整原本的排隊先後順序
    - 完成後重導回我的報名清單網址
    """
    name = request.form.get('name')
    phone = request.form.get('phone', '')
    student_id = request.form.get('student_id') # 為了重導回對應的列表頁
    
    if not name:
        flash('姓名不可空白', 'error')
    else:
        try:
            RegistrationModel.update(reg_id, name, phone)
            flash('聯絡資料更新成功', 'success')
        except Exception:
            flash('資料更新失敗，請聯絡主辦方', 'error')
            
    if student_id:
        return redirect(url_for('registrations.my_registrations', student_id=student_id))
    return redirect(url_for('events.index'))

@registrations_bp.route('/registrations/<int:reg_id>/cancel', methods=['POST'])
def cancel_registration(reg_id):
    """
    逢甲學生/核心機制用：取消目前名單中的報名行為
    - 系統觸發邏輯：要是自己是成功報名者，退位後就順拉下一位進入正取。
    - 重新引導回管理名單內重刷畫面
    """
    student_id = request.form.get('student_id')
    try:
        RegistrationModel.delete(reg_id)
        flash('已成功為您取消報名，名額系統將自動遞補下一位候補同學。', 'success')
    except Exception:
        flash('取消失敗，請聯絡主辦單位', 'error')
        
    if student_id:
        return redirect(url_for('registrations.my_registrations', student_id=student_id))
    return redirect(url_for('events.index'))
