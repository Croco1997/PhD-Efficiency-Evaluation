import pandas as pd
from collections import defaultdict
import os
import networkx as nx
from networkx import DiGraph, density
from networkx.algorithms import global_efficiency

def calculate_global_efficiency(graph):  # 添加括号和参数
    """计算全局效率"""
    if isinstance(graph, DiGraph):
        # 将有向图转换为无向图
        undirected_graph = graph.to_undirected()
        return global_efficiency(undirected_graph)
    else:
        return global_efficiency(graph)

def check_steps_1_3():
    """检查前三步是否完成"""
    folder_exists = os.path.exists('综合邻接矩阵文件夹')
    task_list_exists = os.path.exists('1按时间排列的运行任务列表.csv')
    info_list_exists = os.path.exists('2按时间排列的运行信息列表.csv')
    return folder_exists and task_list_exists and info_list_exists

def check_steps_4_6():
    """检查四到六步是否完成"""
    files = [
        '3按时间排列的节点度数（运行信息数量）.csv',
        '4按时间排列的节点运行成本.csv',
        '5按时间排列的节点运行效率.csv',
        '6按时间排列的网络运行效率.csv'
    ]
    return all(os.path.exists(f) for f in files)

def check_step_7():
    """检查第七步是否完成"""
    return os.path.exists('7按时间排列的子网络运行效率.csv')

def check_step_8():
    """检查第八步是否完成"""
    files = [
        '8按时间排列的网络特征值.csv'
    ]
    return all(os.path.exists(f) for f in files)


# 第一轮检查：前三个步骤
if not check_steps_1_3():
    # 第一步：读取运行任务时间设置
    df = pd.read_excel('A运行任务记录.xlsx')

    # 提取 Code 和 Time 列
    data = df[['Code', 'Time']]

    # 创建一个默认字典，用于存储每个时间点的任务
    task_list = defaultdict(list)

    # 遍历每一行
    for index, row in data.iterrows():
        code = row['Code']
        time_ranges = row['Time'].split('、')
        for time_range in time_ranges:
            start_time_str, end_time_str = time_range.replace('h', '').split('-')
            start_time = float(start_time_str)
            end_time = float(end_time_str)
            current_time = start_time
            while current_time < end_time:
                task_list[round(current_time, 1)].append(code)
                current_time += 0.1

    # 将字典转换为 DataFrame
    result_df = pd.DataFrame(list(task_list.items()), columns=['Time', 'Running_Tasks'])

    # 按照 Time 列进行升序排序
    result_df.sort_values(by='Time', inplace=True)

    # 重置索引
    result_df.reset_index(drop=True, inplace=True)

    # 将结果保存为 CSV 文件
    task_list_csv_path = '1按时间排列的运行任务列表.csv'
    result_df.to_csv(task_list_csv_path, index=False)
    print("第一步完成")  

    # 第二步：读取运行任务的信息需求
    # 读取文件“B运行任务的信息需求”，建立映射关系
    info_req_df = pd.read_excel('B运行任务的信息需求.xlsx')
    task_info_mapping = {}
    for index, row in info_req_df.iterrows():
        task_code = row['Subtask'].strip().upper()
        info_codes = [code.strip().upper() for code in row['Information'].split('、')]
        task_info_mapping[task_code] = info_codes

    # 读取上一步骤生成的文件“按时间排列的运行任务列表”
    task_list_df = pd.read_csv(task_list_csv_path)

    # 定义函数，处理每个时间点的运行任务并获取对应的运行信息代号
    def get_info_codes(task_list_str):
        task_list = [task.strip().strip("'").upper() for task in task_list_str.strip('[]').split(',') if task.strip()]
        all_info_codes = []
        for task in task_list:
            if task in task_info_mapping:
                all_info_codes.extend(task_info_mapping[task])
        if not all_info_codes:
            return '无对应信息'
        return all_info_codes

    # 应用函数获取每个时间点对应的运行信息代号
    task_list_df['Running_Info_Codes'] = task_list_df['Running_Tasks'].apply(get_info_codes)

    # 输出新的文件“按时间排列的运行信息列表”
    output_file_path = '2按时间排列的运行信息列表.csv'
    task_list_df.to_csv(output_file_path, index=False, encoding='utf-8-sig')
    print("第二步完成") 

    # 第三步：生成综合邻接矩阵
    step2_output_file = '2按时间排列的运行信息列表.csv'
    adj_matrix_file = 'C运行信息对应的邻接矩阵.xlsx'
    output_folder = '综合邻接矩阵文件夹'
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    step2_df = pd.read_csv(step2_output_file)
    excel_file = pd.ExcelFile(adj_matrix_file)

    for index, row in step2_df.iterrows():
        time_point = row['Time']
        info_codes = row['Running_Info_Codes']
        if info_codes == '无对应信息':
            continue

        info_codes = info_codes.replace('[', '').replace(']', '').replace("'", "").split(', ')
        combined_matrix = pd.DataFrame()
        for info_code in info_codes:
            info_code = info_code.strip()
            if info_code:
                try:
                    matrix = excel_file.parse(info_code)
                    matrix.set_index(matrix.columns[0], inplace=True)
                    matrix = matrix.apply(pd.to_numeric, errors='coerce').fillna(0)
                    
                    if combined_matrix.empty:
                        combined_matrix = matrix.copy()
                    else:
                        combined_matrix = combined_matrix.add(matrix, fill_value=0).fillna(0)
                        
                except KeyError:
                    print(f'运行信息代号 {info_code} 在文件中未找到对应的 sheet，已跳过。')

        if not combined_matrix.empty:
            output_file_path = os.path.join(output_folder, f'{time_point}_综合邻接矩阵.csv')
            combined_matrix.to_csv(output_file_path)
    print("第三步完成")


# 第二轮检查：四到六步
if not check_steps_4_6():
    print(f'前三步完成')
    # 第四步：计算节点度数（运行信息数量）
    output_folder = '综合邻接矩阵文件夹'
    matrix_files = os.listdir(output_folder)

    # 存储结果的数据
    result_data = []
    node_codes = None

    for matrix_file in matrix_files:
        file_path = os.path.join(output_folder, matrix_file)
        matrix_df = pd.read_csv(file_path, index_col=0)

        # 提取时间点
        time_point = matrix_file.replace('_综合邻接矩阵.csv', '')

        # 计算行和与列和
        row_sums = matrix_df.sum(axis=1)
        col_sums = matrix_df.sum(axis=0)

        # 提取节点代号
        if node_codes is None:
            node_codes = matrix_df.index.tolist()

        # 计算每个节点的输入输出总数
        node_info_counts = []
        for node in node_codes:
            input_count = col_sums[node]
            output_count = row_sums[node]
            node_info_counts.append(input_count + output_count)

        # 添加到结果数据中
        result_data.append([time_point] + node_info_counts)

    # 创建结果 DataFrame
    result_df = pd.DataFrame(result_data, columns=['Time'] + node_codes)

    # 将 Time 列转换为数值类型后进行升序排序
    result_df['Time'] = pd.to_numeric(result_df['Time'])
    result_df = result_df.sort_values(by='Time').reset_index(drop=True)

    # 输出新文件
    output_file_path = '3按时间排列的节点度数（运行信息数量）.csv'
    result_df.to_csv(output_file_path, index=False)

    print(f'第四步完成，结果已保存到 {output_file_path}')

    # 第五步：计算节点运行成本和运行效率
    # 读取按时间排列的节点度数（运行信息数量）
    node_info_df = pd.read_csv('3按时间排列的节点度数（运行信息数量）.csv')
    # 读取社会节点成本记录
    social_cost_df = pd.read_excel('D社会节点成本记录.xlsx')
    social_node_set = set(social_cost_df['Code'])
    # 读取技术节点成本记录
    tech_cost_df = pd.read_excel('E技术节点成本记录.xlsx')
    tech_node_set = set(tech_cost_df['Code'])
    # 读取节点运行容量赋值文件
    capacity_df = pd.read_excel('F节点运行容量赋值.xlsx')
    node_capacity_mapping = {row[0]: row[1] for _, row in capacity_df.iterrows()}

    # 计算每个节点在每个时刻的运行成本
    node_cost_list = []
    for index, row in node_info_df.iterrows():
        time = row['Time']
        cost_row = {'Time': time}
        for col in node_info_df.columns[1:]:
            node = col
            if node in social_node_set:
                base_salary = social_cost_df[social_cost_df['Code'] == node]['Salary'].values[0]
                performance_coefficient = social_cost_df[social_cost_df['Code'] == node]['Performance coefficient'].values[0]
                info_count = row[col]
                cost = base_salary + performance_coefficient * info_count
            elif node in tech_node_set:
                acquisition_cost = tech_cost_df[tech_cost_df['Code'] == node]['Acquisition cost'].values[0]
                depreciation_cycle = tech_cost_df[tech_cost_df['Code'] == node]['Depreciation cycle'].values[0]
                single_maintenance_cost = tech_cost_df[tech_cost_df['Code'] == node]['Single maintenance cost'].values[0]
                maintenance_interval_period = tech_cost_df[tech_cost_df['Code'] == node]['Maintenance interval period'].values[0]
                maintenance_cost_coefficient = tech_cost_df[tech_cost_df['Code'] == node]['Maintenance cost coefficient'].values[0]
                info_count = row[col]
                cost = acquisition_cost / depreciation_cycle + single_maintenance_cost / maintenance_interval_period + \
                    maintenance_cost_coefficient * info_count
            else:
                cost = None
            cost_row[node] = cost
        node_cost_list.append(cost_row)
    node_cost_df = pd.DataFrame(node_cost_list)

    # 按照 Time 列进行升序排序
    node_cost_df.sort_values(by='Time', inplace=True)

    # 输出文件
    node_cost_df.to_csv('4按时间排列的节点运行成本.csv', index=False)

    # 计算每个节点的运行效率
    node_efficiency_list = []
    for index, row in node_info_df.iterrows():
        time = row['Time']
        efficiency_row = {'Time': time}
        for col in node_info_df.columns[1:]:
            node = col
            info_count = row[col]
            capacity = node_capacity_mapping.get(node)
            if cost is not None and cost != 0 and capacity is not None and capacity != 0:
                efficiency = info_count / (cost * capacity)
            else:
                efficiency = None
            efficiency_row[node] = efficiency
        node_efficiency_list.append(efficiency_row)
    node_efficiency_df = pd.DataFrame(node_efficiency_list)

    # 按照 Time 列进行升序排序
    node_efficiency_df.sort_values(by='Time', inplace=True)

    # 输出文件
    node_efficiency_df.to_csv('5按时间排列的节点运行效率.csv', index=False)

    print(f'第五步完成，节点运行成本已保存到 4按时间排列的节点运行成本.csv，节点运行效率已保存到 5按时间排列的节点运行效率.csv')

    # 第六步：计算网络整体效率
    # 读取节点权重赋值文件
    weight_df = pd.read_excel('G节点权重及属性.xlsx')
    node_weight_mapping = {row['Code']: row['Weight'] for _, row in weight_df.iterrows()}

    # 读取按时间排列的节点运行效率文件
    node_efficiency_df = pd.read_csv('5按时间排列的节点运行效率.csv')

    # 计算每个时间点的网络整体效率
    network_efficiency_list = []
    for index, row in node_efficiency_df.iterrows():
        time = row['Time']
        total_efficiency = 0
        for node, weight in node_weight_mapping.items():
            if node in node_efficiency_df.columns:
                node_efficiency = row[node]
                if pd.notna(node_efficiency):
                    total_efficiency += node_efficiency * weight
        network_efficiency_list.append([time, total_efficiency])

    # 创建结果 DataFrame
    network_efficiency_df = pd.DataFrame(network_efficiency_list, columns=['Time', 'Network_Efficiency'])

    # 按照 Time 列进行升序排序
    network_efficiency_df.sort_values(by='Time', inplace=True)

    # 输出文件
    network_efficiency_df.to_csv('6按时间排列的网络运行效率.csv', index=False)

    print(f'第六步完成，网络运行效率已保存到 6按时间排列的网络运行效率.csv')

# 第三轮检查：第七步
if not check_step_7():
    print(f'前六步完成')
    # （1）读取“G节点权重及属性”文件中的第三列内容，设置每个节点的分类属性
    weight_attribute_df = pd.read_excel('G节点权重及属性.xlsx')
    node_type_mapping = {row['Code']: row.iloc[2] for _, row in weight_attribute_df.iterrows()}

    # （2）在第三步生成的“综合邻接矩阵文件夹”的基础上，对每个邻接矩阵文件分别保留S-S、S-T、T-S、T-T关系
    output_folder = '综合邻接矩阵文件夹'
    matrix_files = os.listdir(output_folder)

    subnetwork_folders = {
        'SS': 'SS综合邻接矩阵文件夹',
        'ST': 'ST综合邻接矩阵文件夹',
        'TS': 'TS综合邻接矩阵文件夹',
        'TT': 'TT综合邻接矩阵文件夹'
    }

    for folder in subnetwork_folders.values():
        if not os.path.exists(folder):
            os.makedirs(folder)

    for matrix_file in matrix_files:
        file_path = os.path.join(output_folder, matrix_file)
        matrix_df = pd.read_csv(file_path, index_col=0)
        time_point = matrix_file.replace('_综合邻接矩阵.csv', '')

        node_types = {node: node_type_mapping.get(node) for node in matrix_df.index}

        for subnetwork, folder in subnetwork_folders.items():
            subnetwork_matrix = matrix_df.copy()
            for row_node in matrix_df.index:
                for col_node in matrix_df.columns:
                    row_type = node_types[row_node]
                    col_type = node_types[col_node]
                    if f'{row_type}{col_type}' != subnetwork:
                        subnetwork_matrix.loc[row_node, col_node] = 0

            output_file_path = os.path.join(folder, f'{time_point}_综合邻接矩阵.csv')
            subnetwork_matrix.to_csv(output_file_path)

    # （3）与第四步类似，基于（2）中生成的对应的子网络综合邻接矩阵，计算每个子网络随时间排列的节点度数（运行信息数量）
    subnetwork_info_folders = {
        'SS': '按时间排列的SS子网络节点度数（运行信息数量）',
        'ST': '按时间排列的ST子网络节点度数（运行信息数量）',
        'TS': '按时间排列的TS子网络节点度数（运行信息数量）',
        'TT': '按时间排列的TT子网络节点度数（运行信息数量）'
    }

    if not os.path.exists('按时间排列的子网络节点度数（运行信息数量）文件夹'):
        os.makedirs('按时间排列的子网络节点度数（运行信息数量）文件夹')

    for subnetwork, folder in subnetwork_folders.items():
        matrix_files = os.listdir(folder)
        result_data = []
        node_codes = None

        for matrix_file in matrix_files:
            file_path = os.path.join(folder, matrix_file)
            matrix_df = pd.read_csv(file_path, index_col=0)

            # 提取时间点
            time_point = matrix_file.replace('_综合邻接矩阵.csv', '')

            # 计算行和与列和
            row_sums = matrix_df.sum(axis=1)
            col_sums = matrix_df.sum(axis=0)

            # 提取节点代号
            if node_codes is None:
                node_codes = matrix_df.index.tolist()

            # 计算每个节点的输入输出总数
            node_info_counts = []
            for node in node_codes:
                input_count = col_sums[node]
                output_count = row_sums[node]
                node_info_counts.append(input_count + output_count)

            # 添加到结果数据中
            result_data.append([time_point] + node_info_counts)

        # 创建结果 DataFrame
        result_df = pd.DataFrame(result_data, columns=['Time'] + node_codes)

        # 将 Time 列转换为数值类型后进行升序排序
        result_df['Time'] = pd.to_numeric(result_df['Time'])
        result_df = result_df.sort_values(by='Time').reset_index(drop=True)

        # 输出新文件
        output_file_path = os.path.join('按时间排列的子网络节点度数（运行信息数量）文件夹', f'{subnetwork_info_folders[subnetwork]}.csv')
        result_df.to_csv(output_file_path, index=False)

    # （4）与第五步类似，基于（3）中生成的对应的子网络节点度数（运行信息数量），计算每个子网络随时间排列的节点运行效率
    subnetwork_efficiency_folders = {
        'SS': '按时间排列的SS子网络节点运行效率',
        'ST': '按时间排列的ST子网络节点运行效率',
        'TS': '按时间排列的TS子网络节点运行效率',
        'TT': '按时间排列的TT子网络节点运行效率'
    }

    if not os.path.exists('按时间排列的子网络节点运行效率文件夹'):
        os.makedirs('按时间排列的子网络节点运行效率文件夹')

    # 读取社会节点成本记录
    social_cost_df = pd.read_excel('D社会节点成本记录.xlsx')
    social_node_set = set(social_cost_df['Code'])
    # 读取技术节点成本记录
    tech_cost_df = pd.read_excel('E技术节点成本记录.xlsx')
    tech_node_set = set(tech_cost_df['Code'])

    for subnetwork, info_folder in subnetwork_info_folders.items():
        node_info_df = pd.read_csv(os.path.join('按时间排列的子网络节点度数（运行信息数量）文件夹', f'{info_folder}.csv'))
        node_cost_list = []
        for index, row in node_info_df.iterrows():
            time = row['Time']
            cost_row = {'Time': time}
            for col in node_info_df.columns[1:]:
                node = col
                if node in social_node_set:
                    base_salary = social_cost_df[social_cost_df['Code'] == node]['Salary'].values[0]
                    performance_coefficient = social_cost_df[social_cost_df['Code'] == node]['Performance coefficient'].values[0]
                    info_count = row[col]
                    cost = base_salary + performance_coefficient * info_count
                elif node in tech_node_set:
                    acquisition_cost = tech_cost_df[tech_cost_df['Code'] == node]['Acquisition cost'].values[0]
                    depreciation_cycle = tech_cost_df[tech_cost_df['Code'] == node]['Depreciation cycle'].values[0]
                    single_maintenance_cost = tech_cost_df[tech_cost_df['Code'] == node]['Single maintenance cost'].values[0]
                    maintenance_interval_period = tech_cost_df[tech_cost_df['Code'] == node]['Maintenance interval period'].values[0]
                    maintenance_cost_coefficient = tech_cost_df[tech_cost_df['Code'] == node]['Maintenance cost coefficient'].values[0]
                    info_count = row[col]
                    cost = acquisition_cost / depreciation_cycle + single_maintenance_cost / maintenance_interval_period + \
                        maintenance_cost_coefficient * info_count
                else:
                    cost = None
                cost_row[node] = cost
            node_cost_list.append(cost_row)
        node_cost_df = pd.DataFrame(node_cost_list)

        # 按照 Time 列进行升序排序
        node_cost_df.sort_values(by='Time', inplace=True)

        # 计算每个节点的运行效率
        node_efficiency_list = []
        for index, row in node_info_df.iterrows():
            time = row['Time']
            efficiency_row = {'Time': time}
            for col in node_info_df.columns[1:]:
                node = col
                info_count = row[col]
                cost = node_cost_df[node_cost_df['Time'] == time][node].values[0]
                if cost is not None and cost != 0:
                    efficiency = info_count / cost
                else:
                    efficiency = None
                efficiency_row[node] = efficiency
            node_efficiency_list.append(efficiency_row)
        node_efficiency_df = pd.DataFrame(node_efficiency_list)

        # 按照 Time 列进行升序排序
        node_efficiency_df.sort_values(by='Time', inplace=True)

        # 输出文件
        output_file_path = os.path.join('按时间排列的子网络节点运行效率文件夹', f'{subnetwork_efficiency_folders[subnetwork]}.csv')
        node_efficiency_df.to_csv(output_file_path, index=False)

    # （5）与第六步类似，基于（4）中生成的对应的子网络节点运行效率值，计算每个子网络随时间排列的整体运行效率值
    subnetwork_efficiency_files = {
        'SS': '按时间排列的SS子网络节点运行效率',
        'ST': '按时间排列的ST子网络节点运行效率',
        'TS': '按时间排列的TS子网络节点运行效率',
        'TT': '按时间排列的TT子网络节点运行效率'
    }

    # 读取节点权重赋值文件
    weight_df = pd.read_excel('G节点权重及属性.xlsx')
    node_weight_mapping = {row['Code']: row['Weight'] for _, row in weight_df.iterrows()}

    network_efficiency_list = []
    for index in range(len(pd.read_csv(os.path.join('按时间排列的子网络节点运行效率文件夹', f'{subnetwork_efficiency_files["SS"]}.csv')))):
        time = pd.read_csv(os.path.join('按时间排列的子网络节点运行效率文件夹', f'{subnetwork_efficiency_files["SS"]}.csv')).iloc[index]['Time']
        subnetwork_efficiencies = []
        for subnetwork in subnetwork_efficiency_files.keys():
            subnetwork_efficiency_df = pd.read_csv(os.path.join('按时间排列的子网络节点运行效率文件夹', f'{subnetwork_efficiency_files[subnetwork]}.csv'))
            total_efficiency = 0
            for node, weight in node_weight_mapping.items():
                if node in subnetwork_efficiency_df.columns:
                    node_efficiency = subnetwork_efficiency_df.iloc[index][node]
                    if pd.notna(node_efficiency):
                        total_efficiency += node_efficiency * weight
            subnetwork_efficiencies.append(total_efficiency)
        network_efficiency_list.append([time] + subnetwork_efficiencies)

    # 创建结果 DataFrame
    network_efficiency_df = pd.DataFrame(network_efficiency_list, columns=['Time', 'SS子网络', 'ST子网络', 'TS子网络', 'TT子网络'])

    # 按照 Time 列进行升序排序
    network_efficiency_df.sort_values(by='Time', inplace=True)

    # 输出文件
    network_efficiency_df.to_csv('7按时间排列的子网络运行效率.csv', index=False)

    print(f'第七步完成，结果已保存到相应文件夹')

# 第四轮检查：第八步
if not check_step_8():
    print('前七步已完成')
    # 第八步：计算污水处理网络随时间变化的特征值
    # （1）在步骤三输出的网络综合邻接矩阵的基础上，建立网络节点关联矩阵
    output_folder = r'综合邻接矩阵文件夹'  # 使用原始字符串处理路径
    if not os.path.exists(output_folder):
        raise FileNotFoundError(f"目录不存在: {output_folder}")

    matrix_files = sorted(os.listdir(output_folder), key=lambda x: float(x.split('.')[0]))  # 按时间排序
    combined_results = []

    for file in matrix_files:
        file_path = os.path.join(output_folder, file)
        df = pd.read_csv(file_path, index_col=0)
        
        # 校验邻接矩阵格式
        if df.shape[0] != df.shape[1]:
            print(f"文件 {file} 不是方阵，跳过处理")
            continue
        
        # 构建有向图
        G = DiGraph()
        nodes = df.columns.tolist()
        G.add_nodes_from(nodes)
        for i in range(len(nodes)):
            for j in range(len(nodes)):
                if df.iloc[i, j] != 0:
                    G.add_edge(nodes[i], nodes[j])

        
        # 计算网络密度
        network_density = density(G)
            
        # 计算全局效率
        try:
            if nx.is_directed(G):
                undirected_G = G.to_undirected()
                global_efficiency_value = global_efficiency(undirected_G)
            else:
                global_efficiency_value = global_efficiency(G)
        except nx.NetworkXError:
            # 处理非强连通图
            sccs = list(nx.strongly_connected_components(G))
            if len(sccs) == 1:
                global_efficiency_value = global_efficiency(G)
            else:
                # 计算每个强连通分量的全局效率并取平均值
                scc_efficiencies = [global_efficiency(G.subgraph(c)) for c in sccs]
                global_efficiency_value = sum(scc_efficiencies) / len(scc_efficiencies)

        # 计算每个节点的入度和出度
        in_degrees = dict(G.in_degree())
        out_degrees = dict(G.out_degree())

        # 找到最大节点入度和最大节点出度
        max_in_degree = max(in_degrees.values())
        max_out_degree = max(out_degrees.values())

        # 计算所有节点入度和出度的总和
        sum_in_degrees = sum(in_degrees.values())
        sum_out_degrees = sum(out_degrees.values())

        # 计算入度中心势
        in_degree_centrality_potential = (len(G) * max_in_degree - sum_in_degrees) / ((len(G) - 1) * (len(G) - 2))

        # 计算出度中心势
        out_degree_centrality_potential = (len(G) * max_out_degree - sum_out_degrees) / ((len(G) - 1) * (len(G) - 2))

        # 手动计算有向图的聚集系数
        def directed_clustering_coefficient(G):
            clustering_coefficients = []
            for node in G.nodes():
                neighbors = set(G.successors(node)) | set(G.predecessors(node))
                if len(neighbors) < 2:
                    clustering_coefficients.append(0)
                else:
                    triangles = 0
                    for neighbor in neighbors:
                        triangles += len(set(G.successors(node)) & set(G.successors(neighbor))) + \
                                     len(set(G.predecessors(node)) & set(G.predecessors(neighbor)))
                    triangles /= 2  # 每个三角形被计算了两次
                    clustering_coefficients.append(triangles / (len(neighbors) * (len(neighbors) - 1) / 2))
            return sum(clustering_coefficients) / len(clustering_coefficients)

        clustering_coefficient = directed_clustering_coefficient(G)

        # 计算平均距离（适用于有向图）
        try:
            average_distance = nx.average_shortest_path_length(G.to_undirected())
        except nx.NetworkXError:
            # 如果图是非连通的，则计算每个连通分量的平均距离并取平均值
            sccs = list(nx.connected_components(G.to_undirected()))
            scc_distances = [nx.average_shortest_path_length(G.subgraph(c).to_undirected()) for c in sccs if len(c) > 1]
            average_distance = sum(scc_distances) / len(scc_distances) if scc_distances else 0

        # 存储结果
        combined_results.append({
            '时间': file.replace('_综合邻接矩阵.csv', ''),
            '网络密度': network_density,
            '全局效率': global_efficiency_value,
            '平均距离': average_distance,
            '聚集系数': clustering_coefficient,
            '出度中心势': out_degree_centrality_potential,
            '入度中心势': in_degree_centrality_potential
        })

    # 将结果保存到一个文件中
    results_df = pd.DataFrame(combined_results)
    results_df.to_csv('8按时间排列的网络特征值.csv', index=False)

    print(f'第八步完成，结果已保存到文件 "8按时间排列的网络特征值.csv"')