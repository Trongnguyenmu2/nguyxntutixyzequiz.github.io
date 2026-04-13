import os
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
# Khóa bí mật cần thiết để session hoạt động
app.config['SECRET_KEY'] = 'khoa_bi_mat_doc_file_txt_123456'

# --- HÀM ĐỌC FILE INPUT.TXT ---
def load_quiz_from_file():
    """
    Đọc file input.txt từ cùng thư mục với app.py và chuyển đổi 
    thành cấu trúc dữ liệu cho game.
    """
    quiz_data = {}
    current_unit = 0
    current_question = {}
    
    # 1. Xác định đường dẫn file an toàn (tránh lỗi No such file)
    # Lấy đường dẫn của file app.py hiện tại
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Nối với tên file input.txt
    file_path = os.path.join(base_dir, 'input.txt')
    
    # Kiểm tra file có tồn tại không
    if not os.path.exists(file_path):
        print(f"⚠️ CẢNH BÁO: Không tìm thấy file tại {file_path}")
        # Trả về dữ liệu mẫu để app không bị sập
        return {}

    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
            
        current_options = {} # Để lưu tạm A, B, C, D
        
        for line in lines:
            line = line.strip()
            if not line: continue # Bỏ qua dòng trống

            # Xử lý dòng UNIT (Ví dụ: "UNIT 1")
            if line.upper().startswith("UNIT"):
                try:
                    # Lấy số 1 từ chuỗi "UNIT 1"
                    current_unit = int(line.split()[1])
                    quiz_data[current_unit] = []
                except:
                    pass 

            # Xử lý dòng Câu hỏi (Ví dụ: "Q: Nội dung...")
            elif line.startswith("Q:"):
                current_question = {
                    "q": line[2:].strip(), # Lấy nội dung sau chữ Q:
                    "options": [],
                    "correct": ""
                }
                current_options = {}

            # Xử lý các dòng Đáp án A, B, C, D
            elif line.startswith("A."): current_options['A'] = line[2:].strip()
            elif line.startswith("B."): current_options['B'] = line[2:].strip()
            elif line.startswith("C."): current_options['C'] = line[2:].strip()
            elif line.startswith("D."): current_options['D'] = line[2:].strip()

            # Xử lý dòng Đáp án đúng (Ví dụ: "ANSWER: A")
            elif line.startswith("ANSWER:"):
                ans_char = line.split(":")[1].strip().upper() # Lấy chữ cái A, B, C hoặc D
                
                # Chỉ lưu khi đã có đủ thông tin câu hỏi
                if current_question and 'A' in current_options:
                    # Chuyển các lựa chọn thành list để dễ hiển thị
                    current_question["options"] = [
                        current_options.get('A', ''),
                        current_options.get('B', ''),
                        current_options.get('C', ''),
                        current_options.get('D', '')
                    ]
                    # Tìm nội dung text của đáp án đúng dựa vào ký tự (ví dụ 'A' -> 'Go')
                    current_question["correct"] = current_options.get(ans_char, "")
                    
                    # Thêm câu hỏi vào danh sách của Unit hiện tại
                    if current_unit > 0:
                        if current_unit not in quiz_data:
                            quiz_data[current_unit] = []
                        quiz_data[current_unit].append(current_question)
                    
                    # Reset biến tạm để chuẩn bị cho câu tiếp theo
                    current_question = {}
                    current_options = {}
                    
        print(f"✅ Đã tải thành công {len(quiz_data)} Unit từ file.")
        return quiz_data

    except Exception as e:
        print(f"❌ Lỗi khi đọc file: {e}")
        return {}

# --- BIẾN TOÀN CỤC LƯU DỮ LIỆU ---
QUIZ_DATA = load_quiz_from_file()

# --- CÁC ROUTES FLASK ---

@app.route("/", methods=['GET', 'POST'])
def index():
    # Load lại file mỗi khi về trang chủ 
    # (Giúp bạn sửa file input.txt xong là cập nhật ngay không cần tắt server)
    global QUIZ_DATA
    QUIZ_DATA = load_quiz_from_file() 
    
    if request.method == 'POST':
        player_name = request.form.get('player_name', 'Người Chơi')
        session['player_name'] = player_name
        
        # Reset các chỉ số chơi
        session['q_index'] = 0
        session['score'] = 0
        session['wrong_answers'] = []
        
        # Kiểm tra xem có Unit 1 để bắt đầu không
        if 1 in QUIZ_DATA and len(QUIZ_DATA[1]) > 0:
            return redirect(url_for('unit_quiz', unit_id=1))
        else:
            return "<h3>Lỗi: File input.txt chưa có dữ liệu cho UNIT 1. Hãy kiểm tra lại file.</h3>"
            
    return render_template("index.html")

@app.route("/unit/<int:unit_id>", methods=['GET', 'POST'])
def unit_quiz(unit_id):
    # Nếu Unit không tồn tại (hoặc đã hết các Unit) -> Về trang chủ hoặc thông báo
    if unit_id not in QUIZ_DATA:
        return f"""
        <div style="text-align:center; margin-top:50px;">
            <h1>🎉 Chúc mừng! Bạn đã hoàn thành tất cả các bài kiểm tra!</h1>
            <a href="{url_for('index')}">Về trang chủ</a>
        </div>
        """

    questions = QUIZ_DATA[unit_id]
    q_index = session.get('q_index', 0)
    
    # --- XỬ LÝ KHI NGƯỜI DÙNG NỘP BÀI (POST) ---
    if request.method == 'POST':
        user_choice = request.form.get('answer')
        
        # Nếu người dùng chưa chọn đáp án mà bấm nộp -> Không làm gì cả
        if not user_choice:
            return redirect(url_for('unit_quiz', unit_id=unit_id))
            
        correct_answer = questions[q_index]['correct']
        
        # Kiểm tra đúng/sai
        if user_choice == correct_answer:
            session['score'] = session.get('score', 0) + 1
        else:
            # Lưu lại câu sai
            wrong_list = session.get('wrong_answers', [])
            wrong_list.append({
                'q': questions[q_index]['q'],
                'user': user_choice,
                'correct': correct_answer
            })
            session['wrong_answers'] = wrong_list
            
        # Chuyển sang câu hỏi tiếp theo
        q_index += 1
        session['q_index'] = q_index
        
        # Nếu đã hết câu hỏi trong Unit này -> Xem kết quả
        if q_index >= len(questions):
            return redirect(url_for('unit_result', unit_id=unit_id))
            
        # Nếu còn câu hỏi -> Tải lại trang này với câu mới
        return redirect(url_for('unit_quiz', unit_id=unit_id))

    # --- HIỂN THỊ CÂU HỎI (GET) ---
    # Lấy câu hỏi hiện tại dựa vào chỉ số q_index
    if q_index < len(questions):
        current_question = questions[q_index]
        return render_template("quiz.html", 
                               unit_id=unit_id,
                               q_number=q_index + 1,
                               total_q=len(questions),
                               question=current_question,
                               player_name=session.get('player_name'))
    else:
        # Phòng trường hợp lỗi chỉ số
        return redirect(url_for('unit_result', unit_id=unit_id))

@app.route("/result/<int:unit_id>")
def unit_result(unit_id):
    # Load lại dữ liệu để đảm bảo tính chính xác
    global QUIZ_DATA
    if not QUIZ_DATA: QUIZ_DATA = load_quiz_from_file()
    
    score = session.get('score', 0)
    total = len(QUIZ_DATA.get(unit_id, []))
    wrong_answers = session.get('wrong_answers', [])
    
    # Kiểm tra xem có Unit tiếp theo không
    next_unit = unit_id + 1
    has_next = next_unit in QUIZ_DATA
    
    return render_template("result.html", 
                           unit_id=unit_id,
                           score=score,
                           total=total,
                           wrong_answers=wrong_answers,
                           player_name=session.get('player_name'),
                           next_unit=next_unit,
                           has_next=has_next)

@app.route("/next_unit/<int:next_unit_id>")
def next_unit_setup(next_unit_id):
    # Reset điểm số và chỉ số câu hỏi cho Unit mới
    session['q_index'] = 0
    session['score'] = 0
    session['wrong_answers'] = []
    return redirect(url_for('unit_quiz', unit_id=next_unit_id))

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5500)
