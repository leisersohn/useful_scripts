import psycopg2
import subprocess

#Define Redshift connection
redshift = psycopg2.connect("dbname=<DB> host=<server> port=5439 user=<user> password=<pass>")

#Import messages to process based on SQL output
cursor = redshift.cursor()
cursor.execute("SELECT MSG_TO, MSG_SUBJECT, MSG_ID, MSG_CONTENT FROM MESSAGES")
result = cursor.fetchall()

#Process each message
for row in result:
    MsgTo = row[0]
    MsgSub = row[1]
    MsgId = int(row[2])
    MsgContent = row[3]

    #Create MIME message code
    MessageCode = """To: %s
Subject: %s
Mime-Version: 1.0;
Content-Type: multipart/related; boundary=border;
--border
Content-Type: text/html; charset=UTF-8;

<html>
<body>
    	<table border="1" id="vertical-1">
        <caption>Email ID: %s</caption>
            <tr>
            	<th>Content</th>
                <td>%s</td>
            </tr>
	</table>
        <img src="cid:logo.png">
</body> 	
</html>
--border
Content-Type: image/png;
Content-Transfer-Encoding: uuencode;

""" % (MsgTo,MsgSub,MsgId,MsgContent)
    #Execute ssmtp with MIME code
    command = 'true | (cat - && echo "%s" && uuencode <path>/source_image.png logo.png && echo -e "\n--border--") | ssmtp %s' % (MessageCode,MsgTo)
    cmd = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = cmd.communicate()
    print (out)
    print (err)