# `scrcpy-input.py` [![License]][gpl3]&nbsp;[![No Maintenance Intended]][no-maintenance]

[gpl3]: https://github.com/epilys/scrcpy-input.py/blob/main/COPYING
[License]: https://img.shields.io/github/license/epilys/scrcpy-input.py?color=white
[No Maintenance Intended]: https://img.shields.io/badge/No%20Maintenance%20Intended-%F0%9F%97%99-red
[no-maintenance]: https://unmaintained.tech/

[`scrcpy`](https://github.com/Genymobile/scrcpy) doesn't support non-ascii (unicode) key input. This tool copies your input to system clipboard and then synchronises it with android's clipboard and pastes it with Alt-v command. Obviously this will overwrite your clipboard contents. Make sure you focus on the text input on the scrcpy window before you attempt to paste.

<table align="center">
	<tbody>
		<tr>
			<td><kbd><img src="./scrcpy-input_demo_a.png" alt="screenshot" height="250"/></kbd></td>
			<td><kbd><img src="./scrcpy-input_demo_b.png" alt="screenshot"  height="250"/></kbd></td>
		</tr>
	</tbody>
</table>
