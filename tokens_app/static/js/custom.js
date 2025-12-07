
document.addEventListener('DOMContentLoaded', function () {
  const rows = document.querySelectorAll('#dataTable tbody tr');
  const form = document.getElementById('tokenForm');
  
  rows.forEach(row => {
    row.addEventListener('click', function () {
      // Снимаем выделение
      rows.forEach(r => r.classList.remove('table-active'));
      // Выделяем текущую
      this.classList.add('table-active');
      var selCard = document.querySelector('.card-clickable.text-bg-success')


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
      if (!selCard) {
        form.label.value = label;
      }
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
        $tableTokenBody.append('<tr><td colspan="5" class="text-center">Токены не обнаружены</td></tr>');
        return;
      }
      // data.forEach(function (item) {
      //   const row = `
      //       <tr data-model="${item.model}" data-sn="${item.serial_num}" data-sn-raw="${item.serial_num_raw}"
      //       data-label="${item.label}" data-min-pin="${item.min_pin_user}" class="table-row">
      //           <td>${item.model}</td>
      //           <td>${item.serial_num_raw}</td>
      //           <td>${item.serial_num}</td>
      //           <td>${item.label}</td>
      //           <td>${item.min_pin_user}</td>
      //       </tr>`;
      //   $tableTokenBody.append(row);
      // });
      data.forEach(function (item) {
        const $tr = $('<tr>')
          .addClass('table-row')
          .attr('data-model', item.model)
          .attr('data-sn', item.serial_num)
          .attr('data-sn-raw', item.serial_num_raw)
          .attr('data-label', item.label)
          .attr('data-min-pin', item.min_pin_user);

        // Заполняем ячейки безопасным текстом
        $('<td>').text(item.model).appendTo($tr);
        $('<td>').text(item.serial_num_raw).appendTo($tr);
        $('<td>').text(item.serial_num).appendTo($tr);
        $('<td>').text(item.label).appendTo($tr);
        $('<td>').text(item.min_pin_user).appendTo($tr);

        $tableTokenBody.append($tr);
      });
      assignRowClickHandlers();

    }).fail(function () {
      $tableTokenBody.html('<tr><td colspan="4" class="text-center text-danger">Ошибка загрузки</td></tr>');
    });
  });


  function assignRowClickHandlers() {
    $('.table-row').off('click').on('click', function () {
      var $target = $('.card-clickable.text-bg-success')

      $form.model.value = $(this).data('model');
      $form.serial_num_raw.value = $(this).data('sn-raw');
      $form.serial_num.value = $(this).data('sn');
      $form.min_pin_user.value = $(this).data('min-pin');
      if (!$target.length) {
        $form.label.value = $(this).data('label');
      }
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

  $('#submit_format').on('click', function () {
    let taskId = 'task_' + Date.now(); // Уникальный ID задачи
    // Закрываем модальное окно
    $('#formatModal').modal('hide');

    let formData = $('#tokenForm').serialize();
    formData += '&task_id=' + taskId;

    $('#progressText').text('Пожалуйста, подождите').removeClass('text-danger');
    $('#text_flash').empty();

    // Отправляем запрос на запуск задачи
    $.post('/start_format', formData, function (response) {
      if (response.status === 'started') {
        // Показываем прогресс‑бар
        $('#progressContainer').removeClass('d-none');
        // Запускаем мониторинг прогресса
        monitorProgress(taskId);
      } else if (response.status === 'error') {
        $('#progressContainer').addClass('d-none');
        const newDiv = document.createElement('div');
        newDiv.className = 'alert alert-danger';
        newDiv.innerHTML = response.error.join('<br>');
        $('#text_flash').prepend(newDiv);
      }

    });
  });

  function monitorProgress(id) {
    const checkInterval = 500;
    const newDiv = document.createElement('div');
    newDiv.className = 'alert alert-danger';

    function checkStatus(iter = 1) {
      $.get('/check_status/' + id, function (data) {
        if (data.status === 'completed') {

          $('#progressText').text('Готово!');
          $('#progressContainer').addClass('d-none');

          newDiv.className = 'alert alert-success';
          newDiv.textContent = `Токен sn_raw ${data.sn_raw} отформатирован.`;
          $('#text_flash').prepend(newDiv);
          $('#link_update').click();

        } else if (data.status === 'error') {

          $('#progressText').text(data.error).addClass('text-danger');
          $('#progressContainer').addClass('d-none');

          newDiv.textContent = data.error;
          $('#text_flash').prepend(newDiv);

        } else if (iter*checkInterval/60000>=1) {

          $('#progressContainer').addClass('d-none');
          newDiv.textContent = 'Ошибка при форматировании, не меняется статус';
          $('#text_flash').prepend(newDiv);

        } else {

          setTimeout(checkStatus, checkInterval, iter+1);

        }
      }).fail(function () {
        // Ошибка при запросе статуса
        $('#progressText').text('Ошибка').addClass('text-danger');

        newDiv.textContent = 'Ошибка.';
        $('#text_flash').prepend(newDiv);
      });
    }

    checkStatus(); // Первый запрос
  }
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
