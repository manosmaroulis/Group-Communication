import signal
import socket
import struct
import threading

group_list= []
send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
send_socket.settimeout(1)



my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_socket.connect(("8.8.8.8", 80))

my_IP= my_socket.getsockname()[0]
print(my_IP)

my_socket.close()

send_socket.bind((str(my_IP),0))
send_socket.listen(1)

my_socket_number = send_socket.getsockname()[1]
my_unique_id = (str(my_IP), str(my_socket_number))


def recmessage(rec_addr):
    if rec_addr is None:
        return None,None

    try:
        rec_data, to_send_address = rec_addr.recvfrom(1024)
        if rec_data.decode() == '':
            return None,None
        return rec_data,to_send_address

    except Exception as ex:
        if ex.__class__ is socket.timeout:
            return None,None


def handler(signum, frame):
    sock.close()
    send_socket.close()
    print("closing")

    exit()


signal.signal(signal.SIGINT, handler)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(1)

multicast_group = "224.0.0.1"  # "224.3.29.71"
server_address = ('', 10000)
#sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(server_address)
group = socket.inet_aton(multicast_group)
mreq = struct.pack('4sL', group, socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)


def member_finder(list, member, mem_addr, group, new_team):

    for i in range(len(list)):

        if list[i][0] == group:
            for j in range(len(list[i][1])):
                if list[i][1][j][0] == member or list[i][1][j][1] == mem_addr or (new_team == 2 and list[i][1][j][1][0] == mem_addr[0]):
                    return True

    return False


def group_name_finder(list,name):

    for i in range(len(list)):
        if list[i][0] == name:
            return True

    return False


def add_member(list,group,member):
    for i in range(len(list)):
        if list[i][0]== group:
            list[i][1].append(member)
            return True

    return False

#serialization gia na steilw to paketo
def group_to_tuple(grp_name, group):

    temp = "#"+str(group[0][0])+"#"
    for i in range(1,len(group)):
        temp = temp + "#"+str(group[i][0])+"#"

    temp= (grp_name,temp)
    # print("i group to tuple ekane afto",temp)
    return temp


def address_to_tcp_match(addr,addr_list):

    for i in range(len(addr_list)):
        if addr_list[i] == addr:
            return i

    return None


def send_to_team(list,group,message,client_sock):
    for i in range(len(list)):
        if list[i][0] == group:
            temp = group_to_tuple(group,list[i][1])
            for j in range(len(list[i][1])):
               # print(list[i][1][j][1])
               #  print("afto stelnw",temp)
                counter=address_to_tcp_match(list[i][1][j][1],cl_adresses)

                #print("to stelnw safton",list[i][1][j][1],"arithmos",counter)
                cl_sockets[counter].send(bytes(str(message), "utf-8")+bytes(str(temp), "utf-8"))

            break


def delete_member(mem_address,group_name,list):
    for i in range(len(list)):
        if list[i][0] == group_name:
            for j in range(len(list[i][1])):
                if list[i][1][j][1] == mem_address:
                    list[i][1].pop(j)
                    ##an einai o teleftaios diagrafw kai to team
                    if len(list[i][1])<1:
                        print("team destroyed")
                        list.pop(i)

                    return True

    return False


cl_sockets = []
cl_adresses = []
my_tcp_sockets = []
delay = []

while True:

    data, address = recmessage(sock)
    if data is not None:


        print("TCP SOCKET",my_socket_number, my_IP)
        # cl_sockets[len(cl_sockets) - 1].listen(1)

        sock.sendto(bytes(str((my_IP, my_socket_number)), 'utf-8'), address)

        #my_data, my_address = recmessage(cl_sockets[i])

    try:
        connection, addr = send_socket.accept()
        connection.settimeout(5)
        cl_sockets.append(connection)
        cl_adresses.append(addr)
        delay.append(0)
    except Exception as ex:
        connection=None

    #edw perimenw kainurgius pelates
    try:
        my_data, my_addr = recmessage(connection)

    except Exception as ex:
        print("den irthe tpt apo kainurgio",ex)

    if my_data is not None:

        take_number = my_data
        my_data = my_data.decode()
        print(my_data)


        if str(my_data[0]) == "+":
            num = int(take_number[1])
            new_name = my_data[int(take_number[2]) + 3:]
            group_name = my_data[3:int(take_number[2]) + 3]

            if group_name_finder(group_list, group_name) is False:
                temp_list = []
                temp = (group_name, temp_list)
                group_list.append(temp)

            if member_finder(group_list, new_name,addr, group_name, num) is False:

                temp = (new_name,addr)

                add_member(group_list, group_name, temp)
                # print(group_list)

                ###eidopoiw tus ipoloipus kai teleftaio ton kainurgio gt egine append
                send_to_team(group_list, group_name, "+",None)
                ###
            else:
                print("name  already exists ")
                connection.send(bytes("dup", "utf-8"))
                cl_sockets.pop(len(cl_sockets)-1)
                cl_adresses.pop(len(cl_adresses)-1)
                delay.pop(len(delay)-1)

        # if str(my_data[0])=="-":
        #     print("error probably")

#edw eksipiretw tus idi iparxodes pleates
    for i in range(len(cl_sockets)):

        try:
            cl_sockets[i].settimeout(1)
            my_data, my_addr = recmessage(cl_sockets[i])

        except Exception as ex:
            print("den irthe tpt apo kainurgio", ex)

        if my_data is not None:
            print(my_data)
            my_data = my_data.decode()

            if len(my_data)>1:
                my_data=my_data.replace('H','')

            if my_data !='' and str(my_data[0]) == "-":
                # print("to steile")
                if delete_member(cl_adresses[i], str(my_data[1:]), group_list):

                    cl_adresses.pop(i)
                    cl_sockets[i].close()
                    cl_sockets.pop(i)
                    print("client deleted")
                    print(group_list)
                    connection=None
                    send_to_team(group_list,str(my_data[1:]),"-",None)
                    delay.pop(i)
                    break

            if str(my_data) == "H" and len(my_data) == 1:
                print("hartbit")
                delay[i] = 0
                continue

        else:
            delay[i] += 1
            if delay[i] > 5:
                print("client drinking coffee closing him")

                temp_grp = ''
                temp_name= ''
                stupid_flag=0
                for k in range(len(group_list)):
                    for n in range(len(group_list[k][1])):

                        if group_list[k][1][n][1] == cl_adresses[i]:
                            temp_grp = group_list[k][0]
                            temp_name=group_list[k][1][n][0]
                            stupid_flag=1
                            break

                    if stupid_flag == 1:
                        stupid_flag=0
                        break

                if delete_member(cl_adresses[i],temp_grp,group_list):
                    send_to_team(group_list,temp_grp,"/",None)
                    print("diagraftike apo to team", temp_grp, "o user", temp_name)
                cl_sockets[i].close()
                cl_sockets.pop(i)
                cl_adresses.pop(i)
                delay.pop(i)
                break


