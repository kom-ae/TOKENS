document.addEventListener('DOMContentLoaded', function () {
  const rows = document.querySelectorAll('#dataTable tbody tr');
  const form = document.getElementById('tokenForm');


  rows.forEach(row => {
    row.addEventListener('click', function () {
      // Снимаем выделение
      rows.forEach(r => r.classList.remove('table-active'));
      // Выделяем текущую
      this.classList.add('table-active');


      // Получаем данные
      const model = this.getAttribute('data-model');
      const sn_raw = this.getAttribute('data-sn-raw');
      const sn = this.getAttribute('data-sn');
      const min_pin = this.getAttribute('data-min-pin');
      const label = this.getAttribute('data-label');

      // Заполняем форму
      form.model.value = model;
      form.serial_num_raw.value = sn_raw;
      form.serial_num.value = sn;
      form.min_pin_user.value = min_pin;
      form.label.value = label;

      //очищает div с сообщениями flask
      const div = document.getElementById('text_flash');
      div.replaceChildren();
    });
  });
});

//запрещает Enter в полях
function handleEnter(event) {
  const isTextInput = event.target.type && ['text', 'email', 'password'].includes(event.target.type);
  if (event.key === 'Enter' && isTextInput) {
    event.preventDefault();
  }
}

// Проверяет выбран ли токен перед открытием модального окна подтверждения
// форматирования токена
document.getElementById('openFormatModalbtn').addEventListener('click', function () {
  const field = document.getElementById('model');
  const value = field.value.trim();

  if (value === '') {
    const div = document.getElementById('text_flash');
    div.replaceChildren()
    // Создаём новый div
    const newDiv = document.createElement('div');
    newDiv.className = 'alert alert-warning';
    newDiv.textContent = 'Не выбран токен!';
    // Добавляем в родительский div
    div.appendChild(newDiv);
    return;
  }
  // Открываем Bootstrap‑модальное окно
  const modal = new bootstrap.Modal(document.getElementById('formatModal'));
  modal.show();
});
