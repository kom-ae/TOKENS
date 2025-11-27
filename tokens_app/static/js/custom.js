
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

$(document).ready(function () {
  const $input = $('#search-input');
  const $results = $('#results');
  const $form = document.getElementById('tokenForm');
  const $tableTokenBody = $('#dataTable tbody');
  const $linkUpdate = $('#link_update');
  const $rows = document.querySelectorAll('#dataTable tbody tr');

  // Функция для назначения обработчиков клика на карточки
  function assignCardClickHandlers() {
    $('.card-clickable').off('click').on('click', function () {
      const samAccountName = $(this).data('samaccountname');

      $form.label.value = samAccountName;
      // Визуальное выделение
      $('.card-clickable').removeClass('text-bg-success');
      $(this).addClass('text-bg-success');
    });
  }

  //Обработчик клика по ссылке Обновить
  $linkUpdate.on('click', function (e) {
    e.preventDefault();
    $.getJSON('/update_tokens', function (data) {
      $tableTokenBody.empty();
      if (data.length === 0) {
        $tableBody.append('<tr><td colspan="4" class="text-center">Нет данных</td></tr>');
        return;
      }
      data.forEach(function (item) {
        const row = `
            <tr data-model="${item.model}" data-sn="${item.serial_num}" data-sn-raw="${item.serial_num_raw}"
            data-label="${item.label}" data-min-pin="${item.min_pin_user}" class="table-row">
                <td>${item.model}</td>
                <td>${item.serial_num_raw}</td>
                <td>${item.serial_num}</td>
                <td>${item.label}</td>
                <td>${item.min_pin_user}</td>
            </tr>`;
        $tableTokenBody.append(row);
      });
      assignRowClickHandlers();

    }).fail(function () {
      $tableTokenBody.html('<tr><td colspan="4" class="text-center text-danger">Ошибка загрузки</td></tr>');
    });
  });


  function assignRowClickHandlers() {
    $('.table-row').off('click').on('click', function () {
      $form.model.value = $(this).data('model');
      $form.serial_num_raw.value = $(this).data('sn-raw');
      $form.serial_num.value = $(this).data('sn');
      $form.min_pin_user.value = $(this).data('min-pin');
      $form.label.value = $(this).data('label');

      $('.table-row').removeClass('table-active');
      $(this).addClass('table-active');

      $('#text_flash').empty();
    });

  }

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
        const cardHtml = `
                    <div class="col">
                      <div class="card card-clickable" data-samaccountname="${item.sAMAccountName}">
                        <div class="card-body">
                        <h5 class="card-title">${item.cn}</h5>
                        <p class="card-text">${item.description || 'Нет описания'}</p>
                        </div>
                        <div class="card-footer">${item.sAMAccountName}</div>
                      </div>
                    </div>`;
        $results.append(cardHtml);
      });

      // Назначаем обработчики после добавления карточек
      assignCardClickHandlers();
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
