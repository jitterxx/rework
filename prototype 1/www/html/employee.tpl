
<br>
<br>
<table>
	<tr>
	% for k in keys:
		 <td> ${k}</td>	
	% endfor
	</tr>
    % for row in obj:
	<tr>
	% for key in keys:
		 <td> ${row.__dict__[key]}</td>
	% endfor
	</tr>
    % endfor
</table>