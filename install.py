#!/usr/bin/env python

import os, glob

cwd = os.getcwd()

jdk = glob.glob('jdk*.tar.gz')
if len(jdk) > 1:
    print 'Too many jdks in directory', jdk
    sys.exit(1)

os.system('tar xfz %s' % jdk[0])

folders = glob.glob('jdk1*')
if len(folders) > 1:
    print 'Too many potential jdk folders'
    sys.exit(1)
if len(folders) == 0:
    print 'No jdk available, download from http://www.oracle.com/technetwork/java/javase/downloads/index.html and put into', cwd
    sys.exit(1)

jdk_path = os.path.join(cwd, folders[0])

os.environ['JRE_HOME'] = jdk_path+'/jre'
os.environ['JAVA_HOME'] = jdk_path

os.environ['PATH'] = cwd + ':/bin:/usr/bin:/sbin:/usr/sbin'
os.environ['LD_LIBRARY_PATH'] = cwd + '/usr/lib:' + cwd + '/usr/lib/python2.7/site-packages'

for dir_ in ('usr', 'downloads', 'builds'):
    try:
        os.mkdir(dir_)
    except OSError:
        # Already exists
        pass
try:
    os.mkdir('usr/lib')
except OSError:
    pass

os.chdir('downloads')

os.system('wget http://www.python.org/ftp/python/2.7.5/Python-2.7.5.tgz')
os.system('wget https://github.com/mrj0/jep/archive/master.zip')
os.system('wget http://search.maven.org/remotecontent?filepath=org/python/jython-standalone/2.5.3/jython-standalone-2.5.3.jar -O ../usr/lib/jython-standalone-2.5.3.jar')


os.chdir('..')
os.chdir('builds')

os.system('tar xfz ../downloads/Python-2.7.5.tgz')
os.chdir('Python-2.7.5')

#data = open('Modules/Setup.dist', 'r').read()
#file_ = open('Modules/Setup', 'w')
#file_.write('*static*\n' + data)
#file_.close()

os.system('./configure --prefix=%s/usr' % cwd)
os.system('make -j 8')
os.system('make install')
os.system('make libpython2.7.so')
os.system('cp libpython2.7.so ../../usr/lib')
os.chdir('..')

os.chdir(os.path.join(cwd, 'builds'))

os.system('unzip ../downloads/master.zip')
os.chdir('jep-master')
os.system('../../usr/bin/python setup.py install')

lib = os.popen('find /lib /usr/lib -name libutil.so\*').readlines()[0].strip()

os.chdir(cwd)
script = open('compare.sh', 'w')
script.write("""#!/bin/sh                                                                                                                                              

cwd=`pwd`
export cwd
LD_LIBRARY_PATH="$cwd/usr/lib:$cwd/usr/lib/python2.7/site-packages:%s/jre/lib/i386/server"
export LD_LIBRARY_PATH
LD_PRELOAD="%s:$cwd/usr/lib/libpython2.7.so"
export LD_PRELOAD
PYTHONHOME="$cwd/usr"
export PYTHONHOME

$cwd/jdk1.7.0_21/bin/javac -classpath usr/lib/jep/jep.jar:usr/lib/jython-standalone-2.5.3.jar compare.java
exec $cwd/jdk1.7.0_21/bin/java -classpath usr/lib/jep/jep.jar:usr/lib/jython-standalone-2.5.3.jar:. compare mytest.py

""" % (jdk_path, lib))
script.close()
os.system('chmod +x compare.sh')
script = open('mytest.py', 'w')
script.write('''import time


def mytest():
    t = time.time()
    for x in range(1000000): x*x
    for y in range(1000000, 2): y*y
    print time.time() - t

for x in range(10):
    mytest()
''')
script.close()
os.system('%s/bin/java -jar usr/lib/jython-standalone-2.5.3.jar -m compileall -l .' % jdk_path)
javafile = open('compare.java', 'w')
javafile.write('''import jep.*;
import org.python.util.PythonInterpreter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.BufferedReader;
import java.util.Date;

public class compare
{
    public static void main(String[] args) throws JepException
    {
  Date start;
	Date end;
	long runtime;
	float runtime_seconds;
	System.out.println("Starting comparison of Jython, Jepp and CPython..");
	System.out.println("Starting with Jep..");
	Jep j;
	start = new Date();
	j = new jep.Jep();
	j.runScript("mytest.py");
	j.close();
	end = new Date();
	runtime = end.getTime() - start.getTime();
	
	System.out.println("Ran in milliseconds: " + Float.toString(runtime));
	System.out.println("Now Jython..");
	start = new Date();
	PythonInterpreter python = new PythonInterpreter();
	python.exec("import mytest");
	end = new Date();
	runtime = end.getTime() - start.getTime();
	
	System.out.println("Ran in milliseconds: " + Long.toString(runtime));
	System.out.println("Now CPython..");
	start = new Date();
	try {
	    Process p=Runtime.getRuntime().exec("usr/bin/python mytest.py");
	    p.waitFor();
	    BufferedReader reader = new BufferedReader(new InputStreamReader(p.getInputStream()));
	    String line=reader.readLine();
	    while(line!=null)
		{
		    System.out.println(line);
		    line=reader.readLine();
		}
	}
	catch(IOException io) {}
	catch(InterruptedException ie) {}
	end = new Date();
	runtime = end.getTime() - start.getTime();
	
	System.out.println("Ran in milliseconds: " + Long.toString(runtime));
    }
}
''')
javafile.close()
print 'Now run ./compare.sh to see how Jep, Jython and CPython compare :)'
