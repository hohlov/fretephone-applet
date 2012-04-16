#!/usr/bin/env python
# the clipboard example and description look at http://www.pygtk.org/pygtk2tutorial/ch-NewInPyGTK2.2.html
# the applet example look at 

import sys

import gtk
import pygtk
import gnomeapplet
import gobject
import re
import string

import thread
import threading

from ttp import word2phons, phonetize

from api import Forvo 

pygtk.require('2.0')

def applet_factory(applet, iid):
  Phonenic(applet,iid)
  return True

class ClipboardInfo:                                                            
    pass

class Phonenic(gnomeapplet.Applet):

  def __init__(self,applet,iid):
    display_name = None
    major_in_out = 1
    minor_in_out = 0

    self.timeout_interval = 1000 * 1 #Timeout set to 1secs
    self.applet = applet

    self.label = gtk.Label("")
    self.label.set_use_markup(True)
    self.label.set_markup("Works?")
    self.applet.add(self.label)

    self.pronounce = False
    self.pronouncing = False
    self.pronounced_word = ""

    self.clipboard = gtk.clipboard_get(selection = "PRIMARY")

    #self.clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
    self.clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_PRIMARY)
    self.clipboard.request_text(self.clipboard_text_received)
    gobject.timeout_add(500, self.fetch_clipboard_info)

    self.applet.show_all()
    self.create_menu(applet)



#-----------------------------------------------------------------------------------


  def create_menu(self, applet):
       if self.pronounce:
          xml="""<popup name="button3">
	<menuitem name="Pronounce" 
          verb="Pronounce" 
          label="* Pronounce" 
          pixtype="stock" 
          pixname="gtk-preferences"/>
         <separator/>
        </popup>"""
       else: 
          xml="""<popup name="button3">
	<menuitem name="Pronounce" 
          verb="Pronounce" 
          label="  Pronounce" 
          pixtype="stock" 
          pixname="gtk-preferences"/>
         <separator/>
        </popup>"""

#<submenu name="Submenu" _label="Su_bmenu">
#<menuitem name="ItemAbout" 
#          verb="About" 
#          label="_About" 
#          pixtype="stock" 
#          pixname="gtk-about"/>
#</submenu>
#</popup>"""

       verbs = [('Pronounce', self.set_pronounce)]
       applet.setup_menu(xml, verbs, None)






  def set_pronounce(self, *arguments):
       self.pronounce = not self.pronounce
       self.create_menu(self.applet)
       #print(self.pronounce)

#-----------------------------------------------------------------------------------







    # signal handler called when clipboard returns target data
  def clipboard_targets_received(self, clipboard, targets, info):
    if targets:
        # have to remove dups since Netscape is broken
        targ = {}
        for t in targets:
           targ[str(t)] = 0
        targ = targ.keys()
        targ.sort()
        info.targets = '\n'.join(targ)
        #self.label.set_markup(word2phons(info.text[:15]))
    else:
        info.targets = None
    tmp_string = ""
    if len(info.text)>0:
      self.label.set_markup(tmp_string + word2phons(info.text.decode("utf8")[:30]).replace("_"," ").replace("&","_")[:30])

      if self.pronounce:
              thread.start_new_thread(self.Pronounce, (info.text.decode("utf8"),False))
    return









  def Pronounce(self, sentence, allword = False):

      if not self.pronouncing:
              self.pronouncing = True
               #words_in_sent = re.compile("(\s)").split(info.text[:30].decode("utf8"))
              #splittin into the words
              words_in_sent = re.compile(r"[\w']+|[.,!?;]",re.UNICODE).findall(sentence.decode("utf8"))
              
              # remaining only words ( removing punctuation )
              words_in_sent = [ word for word in words_in_sent if word[0] not in string.punctuation]
              #words_in_sent = (info.text[:30]).decode("utf8").split()

              #print words_in_sent
              if len(words_in_sent)> 0 and self.pronounced_word != words_in_sent[0]:
                      f = Forvo('')
                      f.pronounce(word = words_in_sent[0].encode("utf8"), language = 'fr', file_name = None)
                      self.pronounced_word = words_in_sent[0]
              self.pronouncing = False







    # singal handler called when the clipboard returns text data
  def clipboard_text_received(self, clipboard, text, data):
    if not text or text == '':
        return
    cbi = ClipboardInfo()
    cbi.text = text
    self.clipboard.request_targets(self.clipboard_targets_received, cbi)
    return







    # get the clipboard text
  def fetch_clipboard_info(self):
    self.clipboard.request_text(self.clipboard_text_received)
    return True




gobject.type_register(Phonenic)



#Very useful if I want to debug. To run in debug mode python hindiScroller.py -d
if len(sys.argv) == 2:
	if sys.argv[1] == "-d": #Debug mode
		main_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		main_window.set_title("Ponetizer Applet")
		main_window.connect("destroy", gtk.main_quit)
		app = gnomeapplet.Applet()
		applet_factory(app,None)
		app.reparent(main_window)
		main_window.show_all()
		gtk.main()
		sys.exit()

#If called via gnome panel, run it in the proper way
if __name__ == '__main__':
  gnomeapplet.bonobo_factory("OAFIID:SampleApplet_Factory", gnomeapplet.Applet.__gtype__, 'French phonetique', '0.1', applet_factory)
