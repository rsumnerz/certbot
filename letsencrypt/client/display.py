import dialog

WIDTH = 72
HEIGHT = 18

class SingletonD(object):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SingletonD, cls).__new__(
                                cls, *args, **kwargs)
        return cls._instance


class Display(SingletonD):
    def generic_notification(self, message, width = WIDTH, height = HEIGHT):
        raise Exception("Error no display defined")
    def generic_menu(self, message, choices, input_text):
        raise Exception("Error no display defined")
    def generic_input(self, message):
        raise Exception("Error no display defined")
    def generic_yesno(self, message, yes_label = "Yes", no_label = "No"):
        raise Exception("Error no display defined")
    def filter_names(self, names):
        raise Exception("Error no display defined")
    def success_installation(self, domains):
        raise Exception("Error no display defined")
    def redirect_by_default(self):
        raise Exception("Error no display defined")
    def gen_https_names(self, domains):
        """
        Returns a string of the domains formatted nicely with https:// prepended
        to each
        """
        result = ""
        if len(domains) > 2:
            for i in range(len(domains)-1):
                result = result + "https://" + domains[i] + ", "
            result = result + "and "
        if len(domains) == 2:
            return "https://" + domains[0] + " and https://" + domains[1]
        if domains:
            result = result + "https://" + domains[len(domains)-1]

        return result

    def display_certs(self, certs):
        raise Exception("Error no display define")

    def confirm_revocation(self, cert):
        raise Exception("Error no display defined")

    def cert_info_frame(self, cert):
        text = "-" * (WIDTH - 4) + "\n"
        text += self.cert_info_string(cert)
        text += "-" * (WIDTH - 4)
        return text

    def cert_info_string(self, cert):
        text = "Subject: %s\n" % cert["subject"]
        text += "SAN: %s\n" % cert["san"]
        text += "Issuer: %s\n" % cert["issuer"]
        text += "Public Key: %s\n" % cert["pub_key"]
        text += "Not Before: %s\n" % str(cert["not_before"])
        text += "Not After: %s\n" % str(cert["not_after"])
        text += "Serial Number: %s\n" % cert["serial"]
        text += "SHA1: %s\n" % cert["fingerprint"]
        return text

    def more_info_cert(self, cert):
        raise Exception("Error no display defined")


class NcursesDisplay(Display):
    import dialog

    def __init__(self):
        self.d = dialog.Dialog()

    def generic_notification(self, message, w = WIDTH, h = HEIGHT):
        self.d.msgbox(message, width = w, height = h)

    def generic_menu(self, message, choices, input_text):

        return self.d.menu(message, choices = choices,
                           width=WIDTH, height=HEIGHT)

    def generic_input(self, message):
        return self.d.inputbox(message)
    
    def generic_yesno(self, message, yes = "Yes", no = "No"):
        a = self.d.yesno(message, HEIGHT, WIDTH)

        return a == self.d.DIALOG_OK
        
    def filter_names(self, names):
        choices = [(n, "", 0) for n in names]
        c, s = self.d.checklist("Which names would you like to activate \
        HTTPS for?", choices=choices)

        return c, s


    def success_installation(self, domains):
        self.d.msgbox("\nCongratulations! You have successfully enabled "
                      + self.gen_https_names(domains) + "!", width=WIDTH)

    def display_certs(self, certs):
        list_choices = [
             (str(i+1),
              "%s | %s | %s" % 
              (str(c["cn"].ljust(WIDTH - 39)), 
               c["not_before"].strftime("%m-%d-%y"), 
               "Installed"),
              0) 
            for i, c in enumerate(certs)]
        
        code, se = self.d.checklist("Which certificates would you like to revoke?",
                           choices = list_choices, help_button=True,
                           help_label="More Info", ok_label="Revoke",
                           width=WIDTH, height=HEIGHT)
        return code, [int(s[0])-1 for s in se]


    def redirect_by_default(self):
        choices = [
            ("Easy", "Allow both HTTP and HTTPS access to these sites"),
            ("Secure", "Make all requests redirect to secure HTTPS access")]

        result = self.d.menu("Please choose whether HTTPS access is required \
        or optional.", width=WIDTH, choices=choices)

        if result[0] != 0:
            return False
        return result[1] == "Secure"

    def confirm_revocation(self, cert):
        text = "Are you sure you would like to revoke the following \
        certificate:\n"
        text += self.cert_info_frame(cert)
        text += "This action cannot be reversed!"
        a = self.d.yesno(text, width=WIDTH, height=HEIGHT)
        return a == self.d.DIALOG_OK

    def more_info_cert(self, cert):
        text = "Certificate Information:\n"
        text += self.cert_info_frame(cert)
        self.d.msgbox(text, width=WIDTH, height=HEIGHT)


class FileDisplay(Display):
    def __init__(self, outfile):
        self.outfile = outfile

    def generic_notification(self, message, width = WIDTH, height = HEIGHT):
        side_frame = '-' * (WIDTH - 4)
        self.outfile.write("\n%s\n%s\n%s\n" % (side_frame, message, side_frame))
        raw_input("Press Enter to Continue")

    def generic_menu(self, message, choices, input_text):
        self.outfile.write("\n%s\n" % message)
        side_frame = '-' * (WIDTH - 4)
        self.outfile.write("%s\n" % side_frame)

        for i, c in enumerate(choices):
            self.outfile.write("%d: %s\n" % (i, c))

        self.outfile.write("%s\n" % side_frame)

        code, selection = self.__get_valid_int_ans("Enter the number of a \
        Certificate Authority (c to cancel): ")

        return code, selection

    def generic_input(self, message):
        ans = raw_input("%s (Enter c to cancel)\n" % message)

        if ans.startswith('c') or ans.startswith('C'):
            return CANCEL, -1
        else:
            return OK, ans

    def generic_yesno(self, message):
        self.outfile.write("\n%s\n" % message)
        ans = raw_input("y/n")
        return ans.startswith('y') or ans.startswith('Y')

    def filter_names(self, names):
        c, s = self.generic_menu(
            "Choose the names would you like to upgrade to HTTPS?",
            names,
            "Select the number of the name (c to cancel): ")

        # Make sure to return a list...
        return c, [s]

    def display_certs(self, certs):
        menu_choices = [(str(i+1), str(c["cn"]) + " - " + c["pub_key"] +
                         " - " + str(c["not_before"])[:-6])
                        for i, c in enumerate(certs)]
        
        self.outfile.write("Which certificate would you like to revoke?\n")
        for c in menu_choices:
            self.outfile.write("%s: %s - %s Signed (UTC): %s\n"
                               % (c[0], c[1], c[2], c[3]))

        return [self.__get_valid_int_ans("Revoke Number (c to cancel): ") - 1]

    def __get_valid_int_ans(self, input_string):
        valid_ans = False

        e_msg = "Please input a number or the letter c to cancel\n"
        while not valid_ans:

            ans = raw_input(input_string)
            if ans.startswith('c') or ans.startswith('C'):
                code = CANCEL
                selection = -1
            else:
                try:
                    selection = int(ans)
                    #TODO add check to make sure it is liess than max
                    if selection < 0:
                        self.outfile.write(e_msg)
                        continue
                    code = OK
                    valid_ans = True
                except ValueError:
                    self.outfile.write(e_msg)

        return code, selection


    def success_installation(self, domains):
        s_f = '*' * (WIDTH - 4)
        msg = "%s\nCongratulations! You have successfully enabled %s!\n%s\n" 
        self.outfile.write(msg % (s_f, self.gen_https_names(domains), s_f))

    def redirect_by_default(self):
        ans = raw_input("Would you like to redirect all \
        normal HTTP traffic to HTTPS? y/n")
        return ans.startswith('y') or ans.startswith('Y')

    def confirm_revocation(self, cert):
        self.outfile.write("Are you sure you would like to revoke \
        the following certificate:\n")
        self.outfile.write(self.cert_info_frame(cert))
        self.outfile("This action cannot be reversed!\n");
        ans = raw_input("y/n")
        return ans.startswith('y') or ans.startswith('Y')

    def more_info_cert(self, cert):
        self.outfile.write("\nCertificate Information:\n")
        self.outfile.write(self.cert_info_frame(cert))

display = None
OK = 0
CANCEL = 1
HELP = "help"


def setDisplay(display_inst):
    global display
    display = display_inst

def generic_notification(message, width = WIDTH, height = HEIGHT):
    display.generic_notification(message, width, height)

def generic_menu(message, choices, input_text):
    return display.generic_menu(message, choices, input_text)

def generic_input(message):
    return display.generic_message(message)

def generic_yesno(message, yes_label = "Yes", no_label = "No"):
    return display.generic_yesno(message, yes_label, no_label)

def filter_names(names):
    return display.filter_names(names)

def display_certs(certs):
    return display.display_certs(certs)

def cert_info_string(cert):
    return display.cert_info_string(cert)

def gen_https_names(domains):
    return display.gen_https_names(domains)

def success_installation(domains):
    return display.success_installation(domains)

def redirect_by_default():
    return display.redirect_by_default()

def confirm_revocation(cert):
    return display.confirm_revocation(cert)

def more_info_cert(cert):
    return display.more_info_cert(cert)
