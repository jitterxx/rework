
<br>
<br>
<table>
    % for row in obj:
	<tr>
	% for key in keys:
		 <td> ${row}${key} ${loop.parent}</td>
	% endfor
	</tr>
    % endfor
</table>
