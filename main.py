#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
개인 일정 관리 비서 터미널 프로그램
사용자가 터미널에서 일정과 할 일을 관리할 수 있는 프로그램입니다.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any

# 명령어 히스토리 기능을 위한 readline 모듈 import
try:
    import readline
    READLINE_AVAILABLE = True
except ImportError:
    # Windows에서는 readline이 기본적으로 없을 수 있음
    READLINE_AVAILABLE = False

class PersonalAssistant:
    def __init__(self, data_file: str = "data.json"):
        self.data_file = data_file
        self.data = self.load_data()
        self.history_file = "command_history.txt"
        self.backup_data = None  # undo를 위한 백업 데이터
        self.last_command = None  # 마지막 실행된 명령 정보
        self.setup_readline()
    
    def create_backup(self, command_info: str) -> None:
        """현재 데이터 상태를 백업하고 명령 정보를 저장합니다."""
        import copy
        self.backup_data = copy.deepcopy(self.data)
        self.last_command = command_info
    
    def undo_last_command(self) -> bool:
        """마지막 명령을 취소하고 이전 상태로 되돌립니다."""
        if self.backup_data is None:
            print("❌ 되돌릴 수 있는 명령이 없습니다.")
            return False
        
        if self.last_command is None:
            print("❌ 되돌릴 수 있는 명령이 없습니다.")
            return False
        
        # 데이터 복원
        self.data = self.backup_data
        
        # 파일에 저장
        if self.save_data():
            print(f"↩️  명령 '{self.last_command}'이(가) 취소되었습니다.")
            # 백업 데이터 초기화 (한 번만 undo 가능)
            self.backup_data = None
            self.last_command = None
            return True
        else:
            print("❌ undo 중 오류가 발생했습니다.")
            return False
    
    def setup_readline(self) -> None:
        """명령어 히스토리 기능을 설정합니다."""
        if not READLINE_AVAILABLE:
            return
        
        # 히스토리 파일 로드
        try:
            if os.path.exists(self.history_file):
                readline.read_history_file(self.history_file)
        except (IOError, OSError):
            pass  # 히스토리 파일 로드 실패시 무시
        
        # 히스토리 최대 길이 설정 (최근 1000개 명령어 보관)
        readline.set_history_length(1000)
        
        # 탭 완성 기능 설정
        readline.parse_and_bind('tab: complete')
        readline.set_completer(self.completer)
    
    def completer(self, text: str, state: int) -> str:
        """탭 완성을 위한 명령어 제안 함수입니다."""
        commands = [
            'add schedule', 'add s', 'add sc', 'add todo', 'add to',
            'list', 'list schedules', 'list s', 'list sc', 'list todos', 'list t', 'list to', 'list all', 'list a',
            'update schedule', 'update s', 'update sc', 'update todo', 'update t', 'update to',
            'done', 'delete', 'del', 'rm', 'undo',
            'help', 'exit'
        ]
        
        matches = [cmd for cmd in commands if cmd.startswith(text)]
        
        if state < len(matches):
            return matches[state]
        else:
            return None
    
    def save_history(self) -> None:
        """명령어 히스토리를 파일에 저장합니다."""
        if not READLINE_AVAILABLE:
            return
        
        try:
            readline.write_history_file(self.history_file)
        except (IOError, OSError):
            pass  # 히스토리 저장 실패시 무시
    
    def load_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """JSON 파일에서 데이터를 로드합니다."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"❌ 데이터 파일 로드 중 오류 발생: {e}")
                return {"schedules": [], "todos": []}
        else:
            return {"schedules": [], "todos": []}
    
    def save_data(self) -> bool:
        """데이터를 JSON 파일에 저장합니다."""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            print(f"❌ 데이터 저장 중 오류 발생: {e}")
            return False
    
    def validate_datetime(self, datetime_str: str) -> bool:
        """날짜 형식이 올바른지 검증합니다."""
        try:
            datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
            return True
        except ValueError:
            return False
    
    def add_schedule(self, task: str, datetime_str: str) -> bool:
        """일정을 추가합니다."""
        if not self.validate_datetime(datetime_str):
            print("❌ 날짜 형식이 올바르지 않습니다. YYYY-MM-DD HH:MM 형식으로 입력해주세요.")
            return False
        
        # 백업 생성 (검증 통과 후)
        self.create_backup(f"add schedule {task} {datetime_str}")
        
        # 중복 확인
        for schedule in self.data["schedules"]:
            if schedule["task"] == task and schedule["datetime"] == datetime_str:
                print(f"❌ 동일한 일정이 이미 존재합니다: {task} ({datetime_str})")
                return False
        
        new_schedule = {
            "task": task,
            "datetime": datetime_str,
            "status": "pending"
        }
        self.data["schedules"].append(new_schedule)
        
        if self.save_data():
            print(f"✅ 일정이 추가되었습니다: {task} ({datetime_str})")
            return True
        return False
    
    def add_todo(self, task: str) -> bool:
        """할 일을 추가합니다."""
        # 백업 생성
        self.create_backup(f"add todo {task}")
        
        # 중복 확인
        for todo in self.data["todos"]:
            if todo["task"] == task:
                print(f"❌ 동일한 할 일이 이미 존재합니다: {task}")
                return False
        
        new_todo = {
            "task": task,
            "status": "pending"
        }
        self.data["todos"].append(new_todo)
        
        if self.save_data():
            print(f"✅ 할 일이 추가되었습니다: {task}")
            return True
        return False
    
    def list_schedules(self) -> None:
        """등록된 일정 목록을 조회합니다."""
        if not self.data["schedules"]:
            print("📅 등록된 일정이 없습니다.")
            return
        
        now = datetime.now()
        one_month_ago = now - timedelta(days=30)
        
        # 날짜별로 정렬
        sorted_schedules = sorted(self.data["schedules"], 
                                 key=lambda x: datetime.strptime(x["datetime"], "%Y-%m-%d %H:%M"))
        
        # 한달 전 이후의 일정만 필터링
        filtered_schedules = []
        for schedule in sorted_schedules:
            schedule_time = datetime.strptime(schedule["datetime"], "%Y-%m-%d %H:%M")
            if schedule_time >= one_month_ago:
                filtered_schedules.append(schedule)
        
        if not filtered_schedules:
            print("📅 최근 한달 내 일정이 없습니다.")
            return
        
        # 지난 일정과 미래 일정 분리
        past_schedules = []
        future_schedules = []
        
        for schedule in filtered_schedules:
            schedule_time = datetime.strptime(schedule["datetime"], "%Y-%m-%d %H:%M")
            if schedule_time < now:
                past_schedules.append(schedule)
            else:
                future_schedules.append(schedule)
        
        # 지난 일정 표시
        if past_schedules:
            print("\n📅 지난 일정:")
            print("-" * 50)
            for i, schedule in enumerate(past_schedules, 1):
                status_icon = "✅" if schedule["status"] == "completed" else "❗"
                time_diff = now - datetime.strptime(schedule["datetime"], "%Y-%m-%d %H:%M")
                days_ago = time_diff.days
                if days_ago == 0:
                    time_str = "오늘"
                elif days_ago == 1:
                    time_str = "어제"
                else:
                    time_str = f"{days_ago}일 전"
                print(f"{i}. {status_icon} {schedule['task']} - {schedule['datetime']} ({time_str}, {schedule['status']})")
        
        # 미래 일정 표시
        if future_schedules:
            print("\n📅 예정된 일정:")
            print("-" * 50)
            for i, schedule in enumerate(future_schedules, 1):
                status_icon = "✅" if schedule["status"] == "completed" else "⏰"
                schedule_time = datetime.strptime(schedule["datetime"], "%Y-%m-%d %H:%M")
                time_diff = schedule_time - now
                days_later = time_diff.days
                if days_later == 0:
                    time_str = "오늘"
                elif days_later == 1:
                    time_str = "내일"
                else:
                    time_str = f"{days_later}일 후"
                print(f"{i}. {status_icon} {schedule['task']} - {schedule['datetime']} ({time_str}, {schedule['status']})")
    
    def list_todos(self) -> None:
        """등록된 할 일 목록을 조회합니다."""
        if not self.data["todos"]:
            print("📝 등록된 할 일이 없습니다.")
            return
        
        print("\n📝 할 일 목록:")
        print("-" * 50)
        
        for i, todo in enumerate(self.data["todos"], 1):
            status_icon = "✅" if todo["status"] == "completed" else "⏳"
            print(f"{i}. {status_icon} {todo['task']} ({todo['status']})")
    
    def list_all(self) -> None:
        """모든 항목을 조회합니다."""
        self.list_schedules()
        self.list_todos()
    
    def update_schedule_status(self, task: str, status: str) -> bool:
        """일정의 상태를 업데이트합니다."""
        if status not in ["completed", "pending"]:
            print("❌ 상태는 'completed' 또는 'pending'만 가능합니다.")
            return False
        
        # 백업 생성
        self.create_backup(f"update schedule {task} {status}")
        
        for schedule in self.data["schedules"]:
            if schedule["task"] == task:
                old_status = schedule["status"]
                schedule["status"] = status
                
                if self.save_data():
                    status_icon = "✅" if status == "completed" else "⏰"
                    print(f"{status_icon} 일정 '{task}'의 상태가 '{old_status}'에서 '{status}'로 변경되었습니다.")
                    return True
                return False
        
        print(f"❌ 일정을 찾을 수 없습니다: {task}")
        return False
    
    def update_todo_status(self, task: str, status: str) -> bool:
        """할 일의 상태를 업데이트합니다."""
        if status not in ["completed", "pending"]:
            print("❌ 상태는 'completed' 또는 'pending'만 가능합니다.")
            return False
        
        # 백업 생성
        self.create_backup(f"update todo {task} {status}")
        
        for todo in self.data["todos"]:
            if todo["task"] == task:
                old_status = todo["status"]
                todo["status"] = status
                
                if self.save_data():
                    status_icon = "✅" if status == "completed" else "⏳"
                    print(f"{status_icon} 할 일 '{task}'의 상태가 '{old_status}'에서 '{status}'로 변경되었습니다.")
                    return True
                return False
        
        print(f"❌ 할 일을 찾을 수 없습니다: {task}")
        return False
    
    def done_todo_by_number(self, number: int) -> bool:
        """번호로 할 일을 완료 처리합니다."""
        if not self.data["todos"]:
            print("❌ 등록된 할 일이 없습니다.")
            return False
        
        if number < 1 or number > len(self.data["todos"]):
            print(f"❌ 올바르지 않은 번호입니다. 1-{len(self.data['todos'])} 범위의 번호를 입력하세요.")
            return False
        
        # 백업 생성 (검증 통과 후)
        todo_task = self.data["todos"][number - 1]["task"]
        self.create_backup(f"done {number} ({todo_task})")
        
        todo = self.data["todos"][number - 1]
        old_status = todo["status"]
        todo["status"] = "completed"
        
        if self.save_data():
            print(f"✅ 할 일 '{todo['task']}'가 완료 처리되었습니다!")
            return True
        return False
    
    def delete_todo_by_number(self, number: int) -> bool:
        """번호로 할 일을 삭제합니다."""
        if not self.data["todos"]:
            print("❌ 등록된 할 일이 없습니다.")
            return False
        
        if number < 1 or number > len(self.data["todos"]):
            print(f"❌ 올바르지 않은 번호입니다. 1-{len(self.data['todos'])} 범위의 번호를 입력하세요.")
            return False
        
        # 백업 생성 (검증 통과 후)
        todo_task = self.data["todos"][number - 1]["task"]
        self.create_backup(f"delete {number} ({todo_task})")
        
        todo = self.data["todos"][number - 1]
        task_name = todo["task"]
        
        # 할 일 삭제
        del self.data["todos"][number - 1]
        
        if self.save_data():
            print(f"🗑️ 할 일 '{task_name}'가 삭제되었습니다.")
            return True
        return False
    
    def toggle_todo_by_number(self, number: int) -> bool:
        """번호로 할 일의 상태를 토글합니다."""
        if not self.data["todos"]:
            print("❌ 등록된 할 일이 없습니다.")
            return False
        
        if number < 1 or number > len(self.data["todos"]):
            print(f"❌ 올바르지 않은 번호입니다. 1-{len(self.data['todos'])} 범위의 번호를 입력하세요.")
            return False
        
        # 백업 생성 (검증 통과 후)
        todo = self.data["todos"][number - 1]
        old_status = todo["status"]
        new_status = "completed" if old_status == "pending" else "pending"
        self.create_backup(f"update todo {number} ({todo['task']}: {old_status} -> {new_status})")
        
        # 상태 토글
        todo["status"] = new_status
        
        if self.save_data():
            status_icon = "✅" if new_status == "completed" else "⏳"
            print(f"{status_icon} 할 일 '{todo['task']}'의 상태가 '{old_status}'에서 '{new_status}'로 변경되었습니다.")
            return True
        return False
    
    def show_help(self) -> None:
        """도움말을 표시합니다."""
        help_text = """
🤖 개인 일정 관리 비서

📌 사용 가능한 명령어:

일정 관리:
  add schedule [일정명] [YYYY-MM-DD HH:MM]    - 일정 추가
  add s [일정명] [YYYY-MM-DD HH:MM]           - 일정 추가 (단축)
  add sc [일정명] [YYYY-MM-DD HH:MM]          - 일정 추가 (단축)
  update schedule [일정명] [completed/pending] - 일정 상태 변경
  update s [일정명] [completed/pending]       - 일정 상태 변경 (단축)
  
할 일 관리:
  add todo [할일명]                          - 할 일 추가
  add to [할일명]                            - 할 일 추가 (단축)
  update todo [번호]                         - 할 일 상태 토글 (pending ↔ completed)
  update todo [할일명] [completed/pending]   - 할 일 상태 지정
  update t [번호]                            - 할 일 상태 토글 (단축)
  done [번호]                                - 할 일 완료 처리 (번호로)
  delete [번호] / del [번호] / rm [번호]       - 할 일 삭제 (번호로)

조회:
  list                                       - 전체 목록 조회 (기본)
  list schedules / list s                    - 일정 목록 조회
  list todos / list t                        - 할 일 목록 조회
  list all / list a                          - 전체 목록 조회

기타:
  undo                                       - 직전 명령 취소
  help                                       - 도움말 표시
  exit                                       - 프로그램 종료

🎯 편의 기능:
  ⬆️⬇️ 화살표 키                              - 이전/다음 명령어 탐색
  Tab 키                                     - 명령어 자동완성
  📅 스마트 일정 표시                         - 지난/미래 일정 구분
  📆 한달 범위 필터                          - 최근 한달 내 일정만 표시

📝 사용 예시:
  add s 회의 2024-05-15 14:00               (단축 명령어)
  add to 빨래하기                           (단축 명령어)
  list                                      (간단 조회)
  done 1                                    (1번 할 일 완료)
  update t 2                                (2번 할 일 상태 토글)
  del 3                                     (3번 할 일 삭제)
  undo                                      (직전 명령 취소)
        """
        print(help_text)
    
    def parse_command(self, command: str) -> bool:
        """명령어를 파싱하고 실행합니다."""
        parts = command.strip().split()
        
        if not parts:
            return True
        
        cmd = parts[0].lower()
        
        if cmd == "help":
            self.show_help()
        elif cmd == "exit":
            return False
        elif cmd == "add":
            if len(parts) < 2:
                print("❌ 명령어가 올바르지 않습니다. 'help' 명령어로 사용법을 확인하세요.")
                return True
            
            sub_cmd = parts[1].lower()
            
            # 단축 명령어 지원
            if sub_cmd.startswith("sc") or sub_cmd == "s":  # schedule
                sub_cmd = "schedule"
            elif sub_cmd.startswith("to"):  # todo
                sub_cmd = "todo"
            
            if sub_cmd == "schedule":
                if len(parts) < 5:
                    print("❌ 일정 추가 형식: add schedule [일정명] [YYYY-MM-DD HH:MM]")
                    print("💡 단축 명령어: add s, add sc")
                    return True
                
                task = parts[2]
                datetime_str = f"{parts[3]} {parts[4]}"
                self.add_schedule(task, datetime_str)
            
            elif sub_cmd == "todo":
                if len(parts) < 3:
                    print("❌ 할 일 추가 형식: add todo [할일명]")
                    print("💡 단축 명령어: add to")
                    return True
                
                task = " ".join(parts[2:])  # 여러 단어로 된 할 일 지원
                self.add_todo(task)
            
            else:
                print("❌ 알 수 없는 추가 명령어입니다.")
                print("💡 사용 가능: schedule(s/sc), todo(to)")
        
        elif cmd == "list":
            # list만 입력하면 list all로 동작
            if len(parts) == 1:
                self.list_all()
                return True
            
            sub_cmd = parts[1].lower()
            
            # 단축 명령어 지원
            if sub_cmd.startswith("sc") or sub_cmd == "s":  # schedules
                sub_cmd = "schedules"
            elif sub_cmd.startswith("to") or sub_cmd == "t":  # todos
                sub_cmd = "todos"
            elif sub_cmd.startswith("a"):  # all
                sub_cmd = "all"
            
            if sub_cmd == "schedules":
                self.list_schedules()
            elif sub_cmd == "todos":
                self.list_todos()
            elif sub_cmd == "all":
                self.list_all()
            else:
                print("❌ 알 수 없는 조회 명령어입니다.")
                print("💡 사용 가능: schedules(s/sc), todos(t/to), all(a)")
        
        elif cmd == "update":
            if len(parts) < 3:
                print("❌ 업데이트 형식:")
                print("  update todo [번호]                     - 할 일 상태 토글")
                print("  update todo [할일명] [completed/pending] - 할 일 상태 지정")
                print("  update schedule [일정명] [completed/pending] - 일정 상태 지정")
                return True
            
            sub_cmd = parts[1].lower()
            
            # 단축 명령어 지원
            if sub_cmd.startswith("sc") or sub_cmd == "s":  # schedule
                sub_cmd = "schedule"
            elif sub_cmd.startswith("to") or sub_cmd == "t":  # todo
                sub_cmd = "todo"
            
            if sub_cmd == "todo":
                # todo 업데이트 처리
                if len(parts) == 3:
                    # update todo [번호] - 상태 토글
                    try:
                        number = int(parts[2])
                        self.toggle_todo_by_number(number)
                    except ValueError:
                        print("❌ 올바른 번호를 입력하거나 상태를 명시하세요.")
                        print("💡 예시: update todo 1 (토글) 또는 update todo 할일명 completed")
                elif len(parts) == 4:
                    # update todo [할일명] [상태] - 기존 방식
                    task = parts[2]
                    status = parts[3].lower()
                    self.update_todo_status(task, status)
                else:
                    print("❌ 올바른 형식이 아닙니다.")
                    print("💡 예시: update todo 1 (토글) 또는 update todo 할일명 completed")
            
            elif sub_cmd == "schedule":
                # schedule 업데이트 처리 (기존 방식 유지)
                if len(parts) < 4:
                    print("❌ 일정 업데이트 형식: update schedule [일정명] [completed/pending]")
                    return True
                task = parts[2]
                status = parts[3].lower()
                self.update_schedule_status(task, status)
            
            else:
                print("❌ 알 수 없는 업데이트 명령어입니다.")
                print("💡 사용 가능: schedule(s/sc), todo(t/to)")
        
        elif cmd == "done":
            if len(parts) < 2:
                print("❌ 완료 형식: done [번호]")
                print("💡 예시: done 1")
                return True
            
            try:
                number = int(parts[1])
                self.done_todo_by_number(number)
            except ValueError:
                print("❌ 올바른 번호를 입력하세요.")
                print("💡 예시: done 1")
        
        elif cmd in ["delete", "del", "rm"]:
            if len(parts) < 2:
                print("❌ 삭제 형식: delete [번호] (또는 del, rm)")
                print("💡 예시: delete 1, del 2, rm 3")
                return True
            
            try:
                number = int(parts[1])
                self.delete_todo_by_number(number)
            except ValueError:
                print("❌ 올바른 번호를 입력하세요.")
                print("💡 예시: delete 1, del 2, rm 3")
        
        elif cmd == "undo":
            self.undo_last_command()
        
        else:
            print(f"❌ 알 수 없는 명령어입니다: {cmd}")
            print("💡 'help' 명령어로 사용법을 확인하세요.")
        
        return True
    
    def run(self) -> None:
        """메인 프로그램 실행 루프입니다."""
        print("🤖 개인 일정 관리 비서에 오신 것을 환영합니다!")
        print("💡 'help' 명령어로 사용법을 확인하세요.")
        print("💡 'exit' 명령어로 프로그램을 종료할 수 있습니다.")
        if READLINE_AVAILABLE:
            print("⬆️⬇️ 화살표 키로 이전 명령어를 탐색할 수 있습니다.")
        print("-" * 50)
        
        while True:
            try:
                command = input("\n📝 명령어를 입력하세요: ").strip()
                
                if not command:
                    continue
                
                if not self.parse_command(command):
                    break
                    
            except KeyboardInterrupt:
                print("\n\n👋 프로그램을 종료합니다.")
                self.save_history()
                break
            except EOFError:
                print("\n\n👋 프로그램을 종료합니다.")
                self.save_history()
                break
        
        # 정상 종료시에도 히스토리 저장
        self.save_history()

def main():
    """메인 함수"""
    assistant = PersonalAssistant()
    assistant.run()

if __name__ == "__main__":
    main() 