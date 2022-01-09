function test(tr, res_list) {
    id = $($(tr)[0]).children('.id_')[0].innerText;
    list = []
    for (val of res_list)
        if (val[0] == id)
            list = val;

    t_body = document.getElementById('error_table').getElementsByTagName('tbody')[0];

    t_body.innerHTML = '';

    success_asin_list = list[1];
    failed_asin_list = list[2];

    console.log(success_asin_list);
    console.log(failed_asin_list);

    for (v of failed_asin_list) {
            tr = document.createElement('tr');
            tr.setAttribute('role', 'row');

            td = document.createElement('td');
            td.innerHTML = '<i class="fa fa-remove" style="color: red;">';
            tr.appendChild(td);

            td = document.createElement('td');
            td.innerText = v[0];
            tr.appendChild(td);

            td = document.createElement('td');
            td.innerText = v[1];
            tr.appendChild(td);

            t_body.appendChild(tr);
    }

    for (v of success_asin_list) {
            tr = document.createElement('tr');
            tr.setAttribute('role', 'row');

            td = document.createElement('td');
            td.innerHTML = '<i class="fa fa-check-circle" style="color: green;">';
            tr.appendChild(td);

            td = document.createElement('td');
            td.innerText = v;
            tr.appendChild(td);
            tr.appendChild(document.createElement('td'));
            t_body.appendChild(tr);
    }
}