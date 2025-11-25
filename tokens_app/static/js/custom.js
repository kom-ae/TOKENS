//поиск пользователей с формированием карточек
$(document).ready(function () {
      const $input = $('#search-input');
      const $results = $('#results');

      $input.on('input', function () {
        const query = $input.val().trim();

        if (query.length < 4) {
          $results.empty();
          return;
        }

        $.getJSON('/search', { q: query, limit: 5 }, function (data) {
          $results.empty();

          if (data.length === 0) {
            $results.append('<p>Ничего не найдено</p>');
            return;
          }

          data.forEach(function (item) {
            $results.append(`
              <div class="col">
                <div class="card card-clickable" data-samaccountname="${item.sAMAccountName}">
                  <div class="card-body">
                    <h5 class="card-title">${item.cn}</h5>
                    <p class="card-text">${item.description || 'Нет описания'}</p>
                  </div>
                  <div class="card-footer">${item.sAMAccountName}</div>
                </div>
              </div>
            `);
          assignClickHandlers();
          });
        });
      });
    });

function assignClickHandlers() {
  const cards = document.querySelectorAll('.card-clickable');
  const form = document.getElementById('tokenForm');
  cards.forEach(card => {
    card.addEventListener('click', function() {
      cards.forEach(c => c.classList.remove('text-bg-success'));
      this.classList.add('text-bg-success');
      const samaccountname = this.getAttribute('data-samaccountname');
      form.label.value = samaccountname;
    });
  });
}

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
