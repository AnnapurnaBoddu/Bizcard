import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
from PIL import Image
import numpy as np
import re
from PIL import Image, ImageDraw
import os
import pyodbc
import pandas as pd



st.set_page_config(layout="wide")
st.markdown("<h1 style='text-align: center; color: blue'>BizCard: Extracting Business Card Data with OCR</h1>", unsafe_allow_html=True)




# CREATING OPTION MENU
with st.sidebar:
    selected = option_menu(None, ["Upload & Extract","Modify"],
                            icons=["cloud-upload","pencil-square"],
                            default_index=0,
                            styles={"nav-link": {"font-size": "20px", "text-align": "center", "margin": "0px",
                                            "--hover-color": "#6495ED"},
                               "icon": {"font-size": "20px"},
                               "container": {"max-width": "6000px"},
                               "nav-link-selected": {"background-color": "#93cbf2"}})


if selected == 'Upload & Extract':
    st.write('')
    st.write('')
    st.markdown("### Upload a Business Card")
    uploaded_image = st.file_uploader("upload here", label_visibility="collapsed", type=["png", "jpeg", "jpg"])
    if uploaded_image is not None:

        # saving the uploaded image into a file
        current_directory = os.getcwd()
        image_dir = current_directory + '\\' + 'uploaded_images'
        os.makedirs(image_dir, exist_ok=True)

        # Get the file name
        file_name = uploaded_image.name
        # Generate a unique filename
        image_path = os.path.join(image_dir, file_name)

        # Save the image to disk
        with open(image_path, "wb") as f:
            f.write(uploaded_image.getvalue())

        reader = easyocr.Reader(['en'])
        image = Image.open(uploaded_image)
        image_np = np.array(image)
        text_read = reader.readtext(image_np)
        info = [i[1] for i in text_read]
        used = []
        data = {"company_name": [],
                "card_holder": [],
                "designation": [],
                "mobile_number": [],
                "email": [],
                "website": [],
                "area": [],
                "city": [],
                "state": [],
                "pin_code": [],
                "image_path": []
                }
        data['image_path'].append(image_path)
        for ind, i in enumerate(info):

            # Card holder name
            if ind == 0:
                data['card_holder'].append(i)
                used.append(i)

            # designation
            elif ind == 1:
                data['designation'].append(i)
                used.append(i)

            # for email
            elif '@' in i:
                data['email'].append(i)
                used.append(i)

            # for mobile number
            elif '-' in i:
                data['mobile_number'].append(i)
                used.append(i)
                if len(data['mobile_number']) == 2:
                    data['mobile_number'] = ' & '.join(data['mobile_number'])

            # for website
            # To get WEBSITE_URL
            if "www " in i.lower() or "www." in i.lower():
                data["website"].append(i)
                used.append(i)
            elif "WWW" in i:
                data["website"].append(info[ind - 1] + "." + info[ind])
                used.append(info[ind])

            # To get COMPANY NAME
            if ind == len(info) - 1 and i == 'St ,' and info[-4] == 'GLOBAL':
                data["company_name"].append(info[-4] + ' ' + info[ind - 1])
            elif ind == len(info) - 1 and i != 'St ,' and info[ind - 1] == 'BORCELLE':
                data['company_name'].append(info[ind - 1] + ' ' + i)
            elif ind == len(info) - 1 and (info[-3] == 'Family' or info[-3] == 'selva'):
                data['company_name'].append(info[-3] + ' ' + i)
            elif ind == len(info) - 1 and i != 'St ,':
                data['company_name'].append(i)


            # To get STATE
            state_match = re.findall("[a-zA-Z]{9} +[0-9]", i)
            if state_match:
                data["state"].append(i[:9])
                used.append(i)
            elif re.findall("^[0-9].+, ([a-zA-Z]+);", i):
                data["state"].append(i.split()[-1])
            if len(data["state"]) == 2:
                data["state"].pop(0)

            # only pincode
            if len(i) >= 6 and i.isdigit():
                data["pin_code"].append(i)
            elif re.findall("[a-zA-Z]{9} +[0-9]", i):
                data["pin_code"].append(i[10:])

            # To get CITY NAME
            match1 = re.findall('.+St , ([a-zA-Z]+).+', i)
            match2 = re.findall('.+St,, ([a-zA-Z]+).+', i)
            match3 = re.findall('^[E].*', i)
            if match1:
                data["city"].append(match1[0])
            elif match2:
                data["city"].append(match2[0])
            elif match3:
                data["city"].append(match3[0])

            # To get AREA
            if re.findall('^[0-9].+, [a-zA-Z]+', i):
                data["area"].append(i.split(',')[0])
            elif re.findall('[0-9] [a-zA-Z]+', i):
                data["area"].append(i)
        c1,c2 = st.columns(2,)
        with c2:
            st.markdown(f"**Company name :** {data['company_name'][0]}")
            st.markdown(f"**Cardholder Name :** {data['card_holder'][0]}")
            st.markdown(f"**Designation :** {data['designation'][0]}")
            st.markdown(f"**Mobile Number :** {data['mobile_number']}")
            st.markdown(f"**Email id :** {data['email'][0]}")
            st.markdown(f"**Website :** {data['website'][0]}")
            st.markdown(f"**Area :** {data['area'][0]}")
            st.markdown(f"**City :** {data['city'][0]}")
            st.markdown(f"**State :** {data['state'][0]}")
            st.markdown(f"**pincode :** {data['pin_code'][0]}")
            st.markdown(f"**Image Path :** {data['image_path'][0]}")

            #st.dataframe(data)
        with c1:
            def draw_boxes(image, text_read, color='yellow', width=2):
                # Create a new image with bounding boxes
                image_with_boxes = image.copy()
                draw = ImageDraw.Draw(image_with_boxes)

                # draw boundaries
                for bound in text_read:
                    p0, p1, p2, p3 = bound[0]
                    draw.line([*p0, *p1, *p2, *p3, *p0], fill=color, width=width)
                return image_with_boxes


            # Function calling
            result_image = draw_boxes(image, text_read)

            # Result image
            st.image(result_image, caption='Captured text')
        col1, col2, col3 = st.columns(3)
        with col2:
            if st.button('save_data'):
                def sql_schemadef():
                    # creating data base
                    server = r'Purna\SQLEXPRESS'
                    database = 'master'
                    username = 'sa'
                    password = 'sqlserver'
                    driver = '{SQL Server}'
                    conn = pyodbc.connect(
                        'DRIVER=' + driver + ';SERVER=' + server + ';DATABASE=' + database + ';UID=' + username + ';PWD=' + password,
                         autocommit=True)
                    cursor = conn.cursor()
                    new_database_name = 'bizcard'
                    cursor.execute('CREATE DATABASE ' + new_database_name)

                    cursor.execute('USE bizcard')

                    # creating tables
                    sql_create_bizcard_table = '''
                        CREATE TABLE bizcard_info (
                           Company_name VARCHAR(255) ,
                           Card_holder VARCHAR(255) ,
                           Designation VARCHAR(255) ,
                           Mobile_number VARCHAR(50),
                           Email VARCHAR(255) ,
                           Website VARCHAR(255) ,
                           Area VARCHAR(255) ,
                           City VARCHAR(255) ,
                           State VARCHAR(255) ,
                           Pin_code VARCHAR(10),
                           Image VARCHAR(255)      
                        )
                        '''
                    cursor.execute(sql_create_bizcard_table)


                server = r'Purna\SQLEXPRESS'  # Server name or IP address
                database = 'master'  # Default database (system database)
                username = 'sa'  # Username
                password = 'sqlserver'  # Password
                driver = '{SQL Server}'
                conn = pyodbc.connect(
                    'DRIVER=' + driver + ';SERVER=' + server + ';DATABASE=' + database + ';UID=' + username + ';PWD=' + password,
                    autocommit=True)
                cursor = conn.cursor()

                # SQL query to check if the database exists
                sql_query = "SELECT name FROM sys.databases WHERE name = ?"
                cursor.execute(sql_query, 'bizcard')
                row = cursor.fetchone()
                if row is None:
                    sql_schemadef()
                cursor.execute('USE bizcard')
                query = '''
                    INSERT INTO bizcard_info(Company_name, Card_holder, Designation, Mobile_number, Email, Website, Area,
                    City, State, Pin_code, Image)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?)
                    '''
                df = pd.DataFrame(data)


                for i, row in df.iterrows():
                    cursor.execute(query,tuple(row))
                    st.write('saves successfully')


if selected == 'Modify':
    server = r'Purna\SQLEXPRESS'
    database = 'master'
    username = 'sa'
    password = 'sqlserver'
    driver = '{SQL Server}'
    conn = pyodbc.connect(
        'DRIVER=' + driver + ';SERVER=' + server + ';DATABASE=' + database + ';UID=' + username + ';PWD=' + password,
        autocommit=True)
    cursor = conn.cursor()
    cursor.execute('USE bizcard')
    st.write('')
    st.write('')
    c1, c2 = st.columns(2)
    with c1:
        sql_query = "SELECT  Card_holder FROM bizcard_info"
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        names = []
        for row in rows:
            names.append(row[0])
        #names = [str(i) for i in rows ]
        selected = st.selectbox('select cardholder name to edit', names, index=None)

        if selected:
            qu = "select * from bizcard_info where Card_holder like ?"
            cursor.execute(qu, selected)
            result = cursor.fetchone()
            company_name = st.text_input("Company Name", result[0])
            card_holder = st.text_input("Cardholder Name", result[1])
            designation = st.text_input(" Designation", result[2])
            mobile_number = st.text_input("Mobile Number", result[3])
            email = st.text_input("Email", result[4])
            website = st.text_input("Website", result[5])
            area = st.text_input("Area", result[6])
            city = st.text_input("City", result[7])
            state = st.text_input("State", result[8])
            pin_code = st.text_input("Pincode", result[9])
            image = st.text_input('Image',result[10])
            if st.button('edit'):
                cursor.execute("""UPDATE bizcard_info SET Company_name=?,Card_holder=?,Designation=?,Mobile_number=?,
                Email=?,Website=?,Area=?,City=?,State=?,Pin_code=?, Image=?
                WHERE card_holder like ?""", (company_name, card_holder, designation, mobile_number, email, website, area,
                                          city, state, pin_code,image, selected))
                st.success('successfully updated')

    with c2:
        sql_query = "SELECT  Card_holder FROM bizcard_info"
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        names = []
        for row in rows:
            names.append(row[0])

        #names = [i for i in rows]
        selected = st.selectbox('select card holder name to delete', names, index=None)
        if st.button('delete'):
            sql_qur = 'select Image from bizcard_info where Card_holder like ?'
            cursor.execute(sql_qur, selected)
            image_path = cursor.fetchone()
            if os.path.exists(image_path[0]):
                # Delete the file
                os.remove(image_path[0])
            sql_qu = 'delete from bizcard_info where Card_holder like ?'
            cursor.execute(sql_qu, selected)
            st.success('Data deleted successfully')




