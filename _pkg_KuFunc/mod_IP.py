'''

Functions to call for VIEWER_INPUT

'''




#------------------------------------------------------------------------------
#-Module Import
#------------------------------------------------------------------------------




import platform
import os
import nuke, nukescripts




#------------------------------------------------------------------------------
#-Header
#------------------------------------------------------------------------------




__VERSION__		= '2.0'
__OS__			= platform.system()
__AUTHOR__	 	= "Tianlun Jiang"
__WEBSITE__		= "jiangovfx.com"
__COPYRIGHT__	= "copyright (c) %s - %s" % (__AUTHOR__, __WEBSITE__)

__TITLE__		= "IP v%s" % __VERSION__



def _version_():
	ver='''

	version 1.0
	- Creating A IP node with preset buttons

	version 2.0
	- set channels to all and copy alpha to output
	- add reset button
	- remove startline to preset buttons

	'''
	return ver




#------------------------------------------------------------------------------
#-Global Variables
#------------------------------------------------------------------------------




PRESET_STR = 'IPSet' 




#-------------------------------------------------------------------------------
#- Main Callable
#-------------------------------------------------------------------------------




def IP():
	'''main callable function'''

	if 'VIEWER_INPUT' not in [n.name() for n in nuke.allNodes('Group')]:
		build_IP()
	else:
		nuke.message("VIEWER_INPUT already exist")




#-------------------------------------------------------------------------------
#-Supporting Functions
#-------------------------------------------------------------------------------




def build_IP():
	'''build IP node'''
	if 'VIEWER_INPUT' in [n.name() for n in nuke.allNodes()]:
		nuke.message('IP already exist')
	else:

		str_autolabel = "\n('exp: %s\\n' % nuke.thisNode()['exp'].value())+('gamma: %s\\n' % nuke.thisNode()['y'].value())+('sat: %s\\n' % nuke.thisNode()['sat'].value())"
		colour_bg = 2135237631
		colour_text = 4289560575

		# Declare Node
		node_IP = nuke.nodes.Group(
			note_font_color = colour_text,
			note_font_size = 48,
			note_font = 'bold',
			tile_color = colour_bg,
			hide_input = True
		)
		node_IP.setName('VIEWER_INPUT')

		# Declare knobs
		k_tab = nuke.Tab_Knob('tb_user', 'ku_IP')
		k_exp = nuke.Double_Knob('exp', 'exposure')
		k_exp_d = nuke.Boolean_Knob('d_exp', 'disable', True)
		k_y = nuke.Double_Knob('y', 'gamma')
		k_y_d = nuke.Boolean_Knob('d_y', 'disable', True)
		k_sat = nuke.Double_Knob('sat', 'saturation')
		k_sat_d = nuke.Boolean_Knob('d_sat', 'disable', True)
		k_div_preset = nuke.Text_Knob('tx_preset', 'preset')
		k_preset_add = nuke.PyScript_Knob('preset_add', '<b>&#43;</b>', 'mod_IP.add_preset()')
		k_preset_remove = nuke.PyScript_Knob('preset_remove', '<b>&#8722;</b>', 'mod_IP.remove_preset()')
		k_reset = nuke.PyScript_Knob('reset', '<b>reset</b>', 'mod_IP.reset()')

		k_exp.setValue(0)
		k_y.setValue(1)
		k_sat.setValue(1)

		for k in [k_exp_d, k_y_d, k_sat_d, k_preset_remove]:
			k.clearFlag(nuke.STARTLINE)
		k_reset.setFlag(nuke.STARTLINE)

		## Add Knobs
		for k in [k_tab, k_exp, k_exp_d, k_y, k_y_d, k_sat, k_sat_d, k_div_preset, k_preset_add, k_preset_remove, k_reset]:
			node_IP.addKnob(k)

		# Add nodes inside IP Group
		with node_IP:
			nuke.createNode('Input', "name Input", inpanel=False)
			nuke.createNode('Multiply', "name _EXPOSURE_ channels all", inpanel=False)
			nuke.createNode('Gamma', "name _GAMMA_ channels all", inpanel=False)
			nuke.createNode('Saturation', "name _SATURATION_ channels all", inpanel=False)
			copy_node = nuke.createNode('Copy', "name _ALPHA_COPY_", inpanel=False)
			copy_node.setInput(0, nuke.toNode('_SATURATION_'))
			copy_node.setInput(1, nuke.toNode('Input'))
			nuke.createNode('Output', "name Output", inpanel=False)

			nuke.toNode('_EXPOSURE_')['value'].setExpression('pow(2,parent.exp)')
			nuke.toNode('_GAMMA_')['value'].setExpression('parent.y')
			nuke.toNode('_SATURATION_')['saturation'].setExpression('parent.sat')

			nuke.toNode('_EXPOSURE_')['disable'].setExpression('parent.d_exp')
			nuke.toNode('_GAMMA_')['disable'].setExpression('parent.d_y')
			nuke.toNode('_SATURATION_')['disable'].setExpression('parent.d_sat')

		node_IP['autolabel'].setValue(str_autolabel)




#-------------------------------------------------------------------------------
#-Button Functions
#-------------------------------------------------------------------------------



def reset():
	"""Reset Parameters"""
	n = nuke.thisNode()
	
	n['exp'].setValue(0)
	n['y'].setValue(1)
	n['sat'].setValue(1)
	n['d_exp'].setValue(1)
	n['d_y'].setValue(1)
	n['d_sat'].setValue(1)


def add_preset():
	'''create preset buttons adds data to tooltip'''
	node = nuke.thisNode()
	node_viewer = nuke.activeViewer().node()

	# Get knob values
	dict_knobs = {}

	dict_knobs['lut'] = node_viewer['viewerProcess'].value()
	dict_knobs['cdl'] = node['cdl'].value() if 'cdl' in node.knobs() else None
	ls_knobs = ['exp', 'y','sat', 'd_exp', 'd_y', 'd_sat']
	for k in ls_knobs:
		dict_knobs[k] = node[k].value()
			
	# Build knob for this preset
	this_preset_idx = preset_idx()
	preset_latest = PRESET_STR+str(this_preset_idx)

	## Label input
	this_preset_label = nuke.getInput('Preset Label (keep it short)', 
									preset_latest.replace(PRESET_STR, PRESET_STR+': '))

	if this_preset_label:
		cmd="mod_IP.apply_preset()"
		k_preset = nuke.PyScript_Knob(preset_latest, this_preset_label, cmd)
		k_preset.setTooltip(str(dict_knobs))
		# if this_preset_idx > 1:
		# 	k_preset.clearFlag(nuke.STARTLINE)
		node.addKnob(k_preset)
		k_preset.setFlag(nuke.STARTLINE)


def apply_preset():
	'''apply presets
	@idx: (int), index for preset to apply
	'''

	node = nuke.thisNode()
	thisPreset = eval(nuke.thisKnob().tooltip())

	for k,v in thisPreset.iteritems():
		if k == 'lut':
			nuke.activeViewer().node()['viewerProcess'].setValue(v)
		elif k == 'cdl' and v != None:
			node[k].setValue(v)
		else:
			node[k].setValue(v)
	

def preset_idx():
	'''finds latest preset button index
	return: int
	'''

	node = nuke.thisNode()
	try:
		idx_latest = int(max([k.split(PRESET_STR)[1] for k in node.knobs() if k.startswith(PRESET_STR)]))+1
	except:
		idx_latest = 1

	return int(idx_latest)


def remove_preset():
	'''remove preset button'''

	node = nuke.thisNode()

	knob_presets = [str(k +' | ' + node.knob(k).label()) for k in node.knobs() if k.startswith(PRESET_STR)]

	p = nukescripts.PythonPanel('Remove A Preset')
	pk_knoblist = nuke.Enumeration_Knob('knoblist', "Delete Preset: ", knob_presets)
	p.addKnob(pk_knoblist)

	if p.showModalDialog():
		knob_delete = node.knob(pk_knoblist.value().split(' | ')[0])
		node.removeKnob(knob_delete)
