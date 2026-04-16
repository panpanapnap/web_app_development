from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from app.models.event import EventModel

events_bp = Blueprint('events', __name__)

@events_bp.route('/')
def index():
    """
    顯示首頁 / 活動列表
    - 取得所有建立的開放活動並展示於入口。
    - 模板：events/index.html
    """
    events = EventModel.get_all()
    return render_template('events/index.html', events=events)

@events_bp.route('/events/create', methods=['GET'])
def create_event_page():
    """
    顯示建立活動的主辦方表單頁面
    - 模板：events/create.html
    """
    return render_template('events/create.html')

@events_bp.route('/events/create', methods=['POST'])
def create_event():
    """
    處理主辦方建立活動的表單送出
    - 驗證輸入內容，呼叫 EventModel 存入資料庫
    - 完成後重導回首頁或剛建立的詳細頁面
    """
    title = request.form.get('title')
    capacity = request.form.get('capacity', type=int)
    deadline = request.form.get('deadline')
    description = request.form.get('description', '')
    location = request.form.get('location', '')

    if not title or not capacity or not deadline:
        flash('標題、人數上限與截止日期為必填欄位', 'error')
        return redirect(url_for('events.create_event_page'))
        
    try:
        new_id = EventModel.create(
            title=title, 
            capacity=capacity, 
            deadline=deadline, 
            description=description, 
            location=location
        )
        flash('成功建立活動！', 'success')
        return redirect(url_for('events.event_detail', event_id=new_id))
    except Exception as e:
        flash('建立活動時發生錯誤，請再試一次', 'error')
        return redirect(url_for('events.create_event_page'))

@events_bp.route('/events/<int:event_id>', methods=['GET'])
def event_detail(event_id):
    """
    顯示特定活動的標題、地點與剩餘名額等詳細概要
    - 包含導向報名流程的按鈕
    - 模板：events/detail.html
    """
    event = EventModel.get_by_id(event_id)
    if not event:
        abort(404)
    return render_template('events/detail.html', event=event)

@events_bp.route('/events/<int:event_id>/edit', methods=['GET'])
def edit_event_page(event_id):
    """
    顯示修改活動內容的主辦方預填表單頁面
    - 模板：events/edit.html
    """
    event = EventModel.get_by_id(event_id)
    if not event:
        abort(404)
    return render_template('events/edit.html', event=event)

@events_bp.route('/events/<int:event_id>/update', methods=['POST'])
def update_event(event_id):
    """
    處理並寫入已被編輯過的活動資料
    - 完成後重導至該活動的詳細頁面
    """
    title = request.form.get('title')
    capacity = request.form.get('capacity', type=int)
    deadline = request.form.get('deadline')
    description = request.form.get('description', '')
    location = request.form.get('location', '')

    if not title or not capacity or not deadline:
        flash('標題、人數上限與截止日期為必填欄位', 'error')
        return redirect(url_for('events.edit_event_page', event_id=event_id))

    try:
        EventModel.update(event_id, title, capacity, deadline, description, location)
        flash('活動資料更新成功！', 'success')
        return redirect(url_for('events.event_detail', event_id=event_id))
    except Exception:
        flash('更新活動時發生錯誤，請重試', 'error')
        return redirect(url_for('events.edit_event_page', event_id=event_id))

@events_bp.route('/events/<int:event_id>/delete', methods=['POST'])
def delete_event(event_id):
    """
    刪除活動功能 (伴隨串聯刪除其擁有的報名資料)
    - 僅供主辦方使用，刪除成功後重導向至首頁
    """
    try:
        EventModel.delete(event_id)
        flash('活動已成功刪除', 'success')
    except Exception:
        flash('刪除失敗，請再試一次', 'error')
    return redirect(url_for('events.index'))
