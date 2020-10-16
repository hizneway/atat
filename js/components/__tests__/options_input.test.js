import { mount } from '@vue/test-utils'

import optionsinput from '../options_input'

import { makeTestWrapper } from '../../test_utils/component_test_helpers'

const SelectWrapperComponent = makeTestWrapper({
  components: {
    optionsinput,
  },
  templatePath: 'select_input_template.html',
  data: function () {
    const { initialvalue, optional } = this.initialData
    return { initialvalue, optional }
  },
})

describe('SelectInput Renders Correctly', () => {
  it('Should initialize checked', () => {
    const wrapper = mount(SelectWrapperComponent, {
      propsData: {
        name: 'testCheck',
        initialData: {
          initialvalue: 'b',
          optional: true,
        },
      },
    })
    expect(wrapper.find('.usa-input select').element.value).toBe('b')
  })

  it('Should initialize unchecked', () => {
    const wrapper = mount(SelectWrapperComponent, {
      propsData: {
        name: 'testCheck',
        initialData: {
          initialvalue: '',
          optional: false,
        },
      },
    })
    expect(wrapper.find('.usa-input select').element.value).toBe('')
  })
})

const RadioWrapperComponent = makeTestWrapper({
  components: {
    optionsinput,
  },
  templatePath: 'radio_input_template.html',
  data: function () {
    const { initialvalue, optional } = this.initialData
    return { initialvalue, optional }
  },
})

describe('RadioInput Renders Correctly', () => {
  it('Should initialize checked', () => {
    const wrapper = mount(RadioWrapperComponent, {
      propsData: {
        name: 'testCheck',
        initialData: {
          initialvalue: 'b',
          optional: true,
        },
      },
    })
    expect(wrapper.find('.usa-input input[value="a"]').element.checked).toBe(
      false
    )
    expect(wrapper.find('.usa-input input[value="b"]').element.checked).toBe(
      true
    )
  })

  it('Should initialize unchecked', () => {
    const wrapper = mount(RadioWrapperComponent, {
      propsData: {
        name: 'testCheck',
        initialData: {
          initialvalue: '',
          optional: false,
        },
      },
    })
    expect(wrapper.find('.usa-input input').element.checked).toBe(false)
  })
})
