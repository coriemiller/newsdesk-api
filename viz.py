from viz_qa import *
import sys

reload(sys)
sys.setdefaultencoding('utf8')

requests.packages.urllib3.disable_warnings()


# response for no errors is different than in viz_qa, empty [] instead of 'good'
def textgears_check(text):
    clean_text = re.sub(r'<.*\\?>', '', text)
    url = 'http://api.textgears.com/check.php?text=' + unidecode(clean_text.replace('"', '').replace('&', '%26')) + '&key=NmN7OLAGeZtPRboc'
    r = requests.get(url)
    results = r.json()
    i = 0
    message = []
    if results['score'] != 100:
        while i < len(results['errors']):
            bad = results['errors'][i]['bad']
            fix = results['errors'][i]['better']
            # omit corrections that just add a space out front, and double quotes
            if bad != ''.join(fix).replace(' ', '') and bad != '"':
                message.append(bad + ' -> ' + ', '.join(fix))
            i += 1
    return message


def source_component_errors(text):
    message = []
    find_as_of_date = re.compile(r'As of .*\.')
    as_of_date_string = find_as_of_date.findall(text)
    # Check for and parse as of date
    if bool(as_of_date_string):
        as_of_date = as_of_date_string[0]
        as_of_date = re.sub(';.*', '', as_of_date.replace('As of ', '').replace('.', '').replace(',', '').replace(' ', ''))
        # Convert possible formats to datetime format
        datetime_object = ''
        try:
            datetime_object = datetime.strptime(as_of_date, '%B%d%Y')
        except ValueError:
            try:
                datetime_object = datetime.strptime(as_of_date, '%Y')
            except ValueError:
                try:
                    datetime_object = datetime.strptime(as_of_date, '%B%Y')
                except ValueError:
                    message = ['No update date visible.']
        # sanity check the date value
        if datetime_object != '':
            if datetime_object.date() <= datetime.today().date() and datetime_object.date() > datetime.strptime('January132008', '%B%d%Y').date():
                message = message
            elif datetime_object.date() > datetime.today().date():
                message = ['According to my crystal ball, your date is in the future...']
            else:
                message = ["You're living in the past. Maybe too far in the past. Your date is before 2008. Double-check it please!"]
    # Check for a refreshed frequency
    else:
        find_refreshed = re.compile(r'Refreshed .*\.')
        refreshed_string = find_refreshed.findall(text)
        if bool(refreshed_string):
            message = []
        else:
            message = ['No update date or frequency refreshed']
    return message


def timeline_labels(timeline_errors):
    response = {}
    if bool(timeline_errors):
        i = 1
        for slide in timeline_errors:
            response_label = 'Timeline slide ' + str(i)
            # filter out slides with no errors
            if ''.join(slide) != 'good' and bool(slide) != False:
                response[response_label] = slide
            i += 1
    return response


def ap_style_us_title(text):
    us_pattern = re.compile(r'(U\.S\.|United States|U\.S)')
    matches = us_pattern.findall(text)
    if matches:
        sentence = 'Change ' + matches[0] + ' to US in title'
        return sentence
    else:
        return ''


def ap_style_us(text):
    us_pattern = re.compile(r'US')
    matches = us_pattern.findall(text)
    if matches:
        return 'Change US to U.S. in non-title text'
    else:
        return ''


def ap_style_numbers(text):
    numbers = re.compile(r' (0|1|2|3|4|5|6|7|8|9) ')
    matches = numbers.findall(text)
    if matches:
        sentence = 'Write out the word for ' + matches[0]
        return sentence
    else:
        return ''


def ap_style(title_text, other_text):
    errors = []
    title_us = ap_style_us_title(title_text)
    if title_us:
        errors.append(title_us)
    numbers_title = ap_style_numbers(title_text)
    if numbers_title:
        errors.append(numbers_title)
    if len(other_text) > 1:
        other_us = ap_style_us(other_text)
        if other_us:
            errors.append(other_us)
        numbers_other = ap_style_numbers(other_text)
        if numbers_other:
            errors.append(numbers_other)
    return errors


class Viz(object):
    def __init__(self, viz_id):
        self.viz_id = viz_id
        self.html = download_viz_html(self.viz_id)
        self.soup = make_soup(self.html)
        self.widgets_json = widgets_json(self.html)
        self.title = self.soup.find("title").string.strip()

        self.title_errors = {"Title errors": textgears_check(self.title)}
        try:
            self.subheader = self.soup.find("div", class_="ww-subheader-input").string.strip()
            self.subheader_errors = {"Subheader errors": textgears_check(self.subheader)}
        except AttributeError:
            self.subheader = ''
            self.subheader_errors = {"Subheader errors": []}
        try:
            self.source_text = self.soup.find("div", class_="ww-source").get_text()
            self.source_text_errors = {"Source text errors": check_source_text(self.soup)}
            self.source_component_errors = {"Source component errors": source_component_errors(self.source_text)}
        except AttributeError:
            self.source_text = ''
            self.source_text_errors = {"Source text errors": []}
            self.source_component_errors = {"Source component errors": ['No source component or old source component']}
        # response is a list of dicts, one dict per slide, so an empty response is a LIST
        self.timeline_errors = {"Timeline errors": timeline_labels(timeline_text(self.widgets_json))}
        self.static_annotation_errors = {"Static annotation errors": static_annotations(self.widgets_json)}
        self.value_labels_errors = {"Value label errors": value_labels(self.widgets_json)}
        self.field_def_errors = {"Field def errors": field_defs(self.widgets_json)}
        self.ap_style_errors = {"AP style errors": ap_style(self.title, self.subheader)}

    def json_response(self):
        response_list = []
        errors_list = [self.title_errors,
                       self.subheader_errors,
                       self.source_component_errors,
                       self.source_text_errors,
                       self.timeline_errors,
                       self.static_annotation_errors,
                       self.value_labels_errors,
                       self.field_def_errors,
                       self.ap_style_errors]
        for error in errors_list:
            if bool(error.values()[0]):
                response_list.append(error)
        return response_list


if __name__ == '__main__':
    # U_S = Viz("gABz9xqsAlv")
    # print U_S.json_response()
    # UnitedStates = Viz("iEm9FYEBiCh")
    # print UnitedStates.ap_style_errors
    # no_us = Viz("4UGebIsZS97")
    # print no_us.ap_style_errors
    test = Viz("j3arxXsNdXf")