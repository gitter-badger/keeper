<pre>
# keeper
console time manager

// пример файла todo
# это тоже комментарий, программа его не смотрит
# вот задача. Она не привязана ко времени и занимает 2 часа
сделать план работ по квест-комнате 2h

# эта задача занимат 20 минут и должна быть выполнена до 23 мая
отправить первую версию программы [<23.05.2015, 20m]

# а это встреча, которая назначена на определенное время и будет занимать 2 часа
встретиться с заказчиком [24.05.2015 14:00, 2h]

/*
Это многострочный комментарий. Задачи можно группиовать по "топикам" вот так
*/

планирование:
    задача 1
    задача 2
реализация:
    задача 3
    задача 4
    
// есть специальние топики, которые не участвуют в расчетах времени - done, debts, optional
// однако, задачи из них можно вытащить через keeper list <topic>    

done:
    попробовать забрать сигнал с регистратора
    
// можно задавать периодические задачи. Например, сон и регулярные планерки
сон [+23:00, 8h]
# понедельник И пятница, без дней между ними, по 2 часа каждый раз
планерка [+понедельник пятница 10:00, 2h]

// все, что не распозналось как атрибуты, считается топиками. Например, так тоже можно отметить выполненную задачу
разобраться с кодировкой под windows [done]

// для планирования книжек был добавлен атрибут "количество страниц". Если в задаче встречается такой атрибут, то 
// на каждуют страницу выделяется по 6 минут. А если среди атрибутов попадается еще и hard, то 12.
// всем книгам добавляется топик books
прочитать Тома Сойера [200p]
дочитать Дифуры эльсгольца [122p, hard, math, учеба]
/* сойер и эльгольц будут выведены по запросу keeper list books. эльсгольц также будет доступен по
 * keeper list hard
 * keeper list math
 * keeper list учеба
*/
// запрос keeper current выполняется как keeper list current. поэтому можно отмечать совсем текущие дела либо помещая
// их в файл current.todo, либо помещая в топик current:, либо выставляя этот топик в атрибутах
</pre>
